import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

from anypc_shelld import games
from anypc_shelld.server import App, serve
from anypc_shelld.store import Store
from anypc_shelld.system import parse_wpctl_volume, split_nmcli

DESKTOP = """[Desktop Entry]
Type=Application
Name={name}
Exec={exec}
Icon=nothing-here
Categories={cats}
{extra}
"""

MANIFEST = """"AppState"
{{
\t"appid"\t\t"{appid}"
\t"name"\t\t"{name}"
}}
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.apps = os.path.join(self.tmp, "apps")
        write(os.path.join(self.apps, "kart.desktop"),
              DESKTOP.format(name="Kart", exec="kart --fullscreen %U", cats="Game;ArcadeGame;", extra=""))
        write(os.path.join(self.apps, "editor.desktop"),
              DESKTOP.format(name="Editor", exec="editor %f", cats="Utility;", extra=""))
        write(os.path.join(self.apps, "hidden.desktop"),
              DESKTOP.format(name="Hidden", exec="hidden", cats="Game;", extra="NoDisplay=true"))
        write(os.path.join(self.apps, "steamshort.desktop"),
              DESKTOP.format(name="Portal Thing", exec="steam steam://rungameid/400", cats="Game;", extra=""))
        self.steam = os.path.join(self.tmp, "Steam")
        write(os.path.join(self.steam, "steamapps", "appmanifest_400.acf"), MANIFEST.format(appid="400", name="Portal Thing"))
        write(os.path.join(self.steam, "steamapps", "appmanifest_1.acf"), MANIFEST.format(appid="1", name="Proton 9.0"))
        lib2 = os.path.join(self.tmp, "lib2")
        write(os.path.join(lib2, "steamapps", "appmanifest_77.acf"), MANIFEST.format(appid="77", name="Far Game"))
        write(os.path.join(self.steam, "steamapps", "libraryfolders.vdf"),
              '"libraryfolders"\n{\n "0"\n {\n  "path" "%s"\n }\n}\n' % lib2)

    def test_desktop_filters_and_exec(self):
        gs = games.scan_desktop([self.apps])
        names = sorted(g["name"] for g in gs)
        self.assertEqual(names, ["Kart", "Portal Thing"])
        kart = next(g for g in gs if g["name"] == "Kart")
        self.assertEqual(kart["launch"]["argv"], ["kart", "--fullscreen"])
        self.assertEqual(kart["genre"], "Arcade")

    def test_steam_libraries_and_skip_tools(self):
        gs = games.scan_steam([self.steam])
        self.assertEqual(sorted(g["name"] for g in gs), ["Far Game", "Portal Thing"])

    def test_scan_all_dedupes_steam_shortcuts(self):
        gs = games.scan_all([self.apps], [self.steam])
        portal = [g for g in gs if g["name"] == "Portal Thing"]
        self.assertEqual(len(portal), 1)
        self.assertEqual(portal[0]["source"], "steam")
        self.assertEqual(games.launch_argv(portal[0]), ["steam", "steam://rungameid/400"])

    def test_compat_switches(self):
        gs = games.scan_all([self.apps], [self.steam], {"steam": False, "native": True})
        self.assertTrue(all(g["source"] != "steam" for g in gs))


class ParserTests(unittest.TestCase):
    def test_nmcli_escapes(self):
        self.assertEqual(split_nmcli(r"*:My\:Net:80:WPA2"), ["*", "My:Net", "80", "WPA2"])

    def test_wpctl(self):
        self.assertEqual(parse_wpctl_volume("Volume: 0.45 [MUTED]"), (45, True))
        self.assertEqual(parse_wpctl_volume("Volume: 1.00"), (100, False))
        self.assertIsNone(parse_wpctl_volume(""))


class StoreTests(unittest.TestCase):
    def test_settings_validation_and_persistence(self):
        path = os.path.join(tempfile.mkdtemp(), "state.json")
        s = Store(path)
        s.update_settings({"reduce_motion": True, "compat": {"anyps5": True}})
        with self.assertRaises(ValueError):
            s.update_settings({"evil": 1})
        with self.assertRaises(ValueError):
            s.update_settings({"reduce_motion": "yes"})
        s2 = Store(path)
        self.assertTrue(s2.settings()["reduce_motion"])
        self.assertTrue(s2.settings()["compat"]["anyps5"])

    def test_users(self):
        s = Store(os.path.join(tempfile.mkdtemp(), "state.json"))
        u = s.add_user("  Vlad  ", "pink")
        self.assertEqual(u["name"], "Vlad")
        self.assertEqual(u["color"], "blue")
        with self.assertRaises(ValueError):
            s.add_user("   ", "blue")


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = tempfile.mkdtemp()
        write(os.path.join(cls.ui, "index.html"), "<!doctype html><p>shell</p>")
        store = Store(os.path.join(tempfile.mkdtemp(), "state.json"))
        cls.app = App(cls.ui, store=store, demo=True, port=0)
        cls.httpd = serve(cls.app, "127.0.0.1", 0)
        cls.port = cls.httpd.server_address[1]
        cls.app.port = cls.port
        # rebuild handler with the real port for the Host check
        from anypc_shelld.server import make_handler
        cls.httpd.RequestHandlerClass = make_handler(cls.app)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def req(self, path, body=None, headers=None):
        h = {"X-AnyPC": "1", "Content-Type": "application/json"}
        h.update(headers or {})
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, headers=h,
                                   method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(r) as resp:
                raw = resp.read()
                return resp.status, (json.loads(raw) if resp.headers.get_content_type() == "application/json" else raw)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_static_and_traversal(self):
        st, body = self.req("/")
        self.assertEqual(st, 200)
        self.assertIn(b"shell", body)
        st, _ = self.req("/../../etc/passwd")
        self.assertEqual(st, 404)

    def test_games_and_launch_cycle(self):
        st, gs = self.req("/api/games")
        self.assertEqual(st, 200)
        self.assertGreater(len(gs), 5)
        gid = gs[0]["id"]
        st, r = self.req(f"/api/games/{gid}/launch", {})
        self.assertEqual((st, r["running"]), (200, True))
        st, _ = self.req(f"/api/games/{gid}/launch", {})
        self.assertEqual(st, 409)
        st, r = self.req("/api/running/stop", {})
        self.assertFalse(r["running"])
        st, gs = self.req("/api/games")
        self.assertGreater(next(g for g in gs if g["id"] == gid)["lastPlayed"], 0)

    def test_post_requires_header(self):
        st, _ = self.req("/api/settings", {"reduce_motion": True}, {"X-AnyPC": "0"})
        self.assertEqual(st, 403)

    def test_bad_host_rejected(self):
        st, _ = self.req("/api/state", headers={"Host": "evil.example"})
        self.assertEqual(st, 403)

    def test_settings_and_audio(self):
        st, s = self.req("/api/settings", {"compat": {"anyps5": True}})
        self.assertEqual(st, 200)
        self.assertTrue(s["compat"]["anyps5"])
        st, _ = self.req("/api/settings", {"compat": {"nope": True}})
        self.assertEqual(st, 400)
        st, a = self.req("/api/audio", {"volume": 150})
        self.assertEqual(a["volume"], 100)

    def test_power_unknown(self):
        st, _ = self.req("/api/power/selfdestruct", {})
        self.assertEqual(st, 400)


if __name__ == "__main__":
    unittest.main()
