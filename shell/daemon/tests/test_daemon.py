import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from anypc_shelld import games
from anypc_shelld.server import App, serve
from anypc_shelld.store import Store
from anypc_shelld import system
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

    def test_anyps5_discovery_relocates_output_and_requires_executable_elf(self):
        home = Path(self.tmp)
        folder = home / "Games" / "AnyPS5" / "Local Homebrew"
        folder.mkdir(parents=True)
        executable = folder / "example.elf"
        # Only the ELF identification bytes are needed to test discovery.
        executable.write_bytes(b"\x7fELF\x02\x01" + bytes(12) + b"\x3e\x00")
        executable.chmod(0o755)
        write(folder / "example.elf.desktop", DESKTOP.format(
            name="Local Homebrew", exec='"/old/folder/example.elf"', cats="Game;",
            extra="Path=/old/folder"))
        (folder / "not-linux.elf").write_bytes(b"MZ")
        (folder / "not-linux.elf").chmod(0o755)
        write(folder / "not-linux.elf.desktop", DESKTOP.format(
            name="Wrong Format", exec="/old/folder/not-linux.elf", cats="Game;", extra=""))
        with patch.object(games, "_home", return_value=str(home)):
            self.assertFalse(any(game["source"] == "anyps5" for game in games.scan_all([self.apps], [self.steam])))
            matches = [game for game in games.scan_all([self.apps], [self.steam], {"anyps5": True})
                       if game["source"] == "anyps5"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["name"], "Local Homebrew")
        self.assertEqual(games.launch_argv(matches[0]), [str(executable.resolve())])
        self.assertEqual(matches[0]["launch"]["cwd"], str(folder.resolve()))


class ParserTests(unittest.TestCase):
    def test_nmcli_escapes(self):
        self.assertEqual(split_nmcli(r"*:My\:Net:80:WPA2"), ["*", "My:Net", "80", "WPA2"])

    def test_wpctl(self):
        self.assertEqual(parse_wpctl_volume("Volume: 0.45 [MUTED]"), (45, True))
        self.assertEqual(parse_wpctl_volume("Volume: 1.00"), (100, False))
        self.assertIsNone(parse_wpctl_volume(""))


WPCTL_STATUS = """PipeWire 'pipewire-0' [1.2.7, player@anypc, cookie:1]
 └─ Clients:
        33. WirePlumber                         [1.2.7, player@anypc, pid:1200]

Audio
 ├─ Devices:
 │      42. Built-in Audio                      [alsa]
 │
 ├─ Sinks:
 │      48. HDMI / DisplayPort 1 Output         [vol: 0.70]
 │  *   52. Built-in Audio Analog Stereo        [vol: 0.40 MUTED]
 │
 ├─ Sources:
 │  *   53. Built-in Audio Analog Stereo        [vol: 1.00]
 │
 └─ Streams:

Video
 ├─ Sinks:
 │      70. Should Not Appear
"""

BOOTC = {"status": {
    "booted": {"image": {"image": {"image": "ghcr.io/x/anypc-os:latest"}, "version": "0.1", "imageDigest": "sha256:aaa"},
               "cachedUpdate": {"version": "0.2", "imageDigest": "sha256:bbb"}},
    "staged": None, "rollback": {"image": {"image": {"image": "ghcr.io/x/anypc-os:latest"}, "version": "0.0.9", "imageDigest": "sha256:ccc"}}}}


class SystemParserTests(unittest.TestCase):
    def test_wpctl_sinks(self):
        sinks = system.parse_wpctl_sinks(WPCTL_STATUS)
        self.assertEqual([s["id"] for s in sinks], [48, 52])
        self.assertTrue(sinks[1]["default"])
        self.assertEqual(sinks[0]["name"], "HDMI / DisplayPort 1 Output")

    def test_bluetooth(self):
        devs = system.parse_bt_devices("Device AA:BB:CC:DD:EE:FF Wireless Controller\nController 11:22 x\n")
        self.assertEqual(devs, [("AA:BB:CC:DD:EE:FF", "Wireless Controller")])
        info = system.parse_bt_info("\tName: Pad\n\tPaired: yes\n\tConnected: no\n\tBattery Percentage: 0x50 (80)\n")
        self.assertEqual((info["Paired"], info["Connected"]), ("yes", "no"))

    def test_bootc(self):
        st = system.parse_bootc_status(BOOTC)
        self.assertEqual(st["booted"]["version"], "0.1")
        self.assertEqual(st["available"]["version"], "0.2")
        self.assertEqual(st["rollback"]["version"], "0.0.9")
        self.assertIsNone(system.parse_bootc_status({})["booted"])

    def test_session_conf_and_display_mode(self):
        d = tempfile.mkdtemp()
        b = system.Backend(d)
        b.displays = lambda: {"outputs": [{"connector": "HDMI-A-1", "modes": ["1920x1080"]}], "mode": "auto"}
        b.set_display_mode("1920x1080")
        self.assertEqual(b.session_conf(), {"ANYPC_WIDTH": "1920", "ANYPC_HEIGHT": "1080"})
        with self.assertRaises(ValueError):
            b.set_display_mode("1920x1080; rm -rf /")
        b.set_display_mode("auto")
        self.assertEqual(b.session_conf(), {})
        self.assertEqual(system.parse_session_conf("ANYPC_WIDTH=1280\nEVIL=$(x)\nANYPC_X=a b\n"), {"ANYPC_WIDTH": "1280"})

    def test_validation(self):
        b = system.Backend(tempfile.mkdtemp())
        for bad in ("", "-x", "a" * 64, "bad name", "x;y"):
            with self.assertRaises(ValueError):
                b.set_hostname(bad)
        with self.assertRaises(ValueError):
            b.bt_action("not-a-mac", "pair")
        with self.assertRaises(ValueError):
            b.bt_action("AA:BB:CC:DD:EE:FF", "explode")
        with self.assertRaises(ValueError):
            b.wifi_connect("x" * 40)
        with self.assertRaises(ValueError):
            b.wifi_connect("Home", "short")

    def test_emulator_source(self):
        tmp = tempfile.mkdtemp()
        write(os.path.join(tmp, "ra.desktop"), DESKTOP.format(name="RetroArch", exec="retroarch", cats="Game;Emulator;", extra=""))
        g = games.scan_desktop([tmp])[0]
        self.assertEqual((g["source"], g["genre"]), ("emulator", "Emulator"))
        self.assertEqual(games.scan_all([tmp], [], {"emulators": False}), [])


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
        with patch.object(self.app.backend, "modules", return_value={"anyps5": {"installed": False}}):
            st, _ = self.req("/api/settings", {"compat": {"anyps5": True}})
            self.assertEqual(st, 422)  # no registered title
        st, s = self.req("/api/settings", {"compat": {"emulators": False}})
        self.assertEqual(st, 200)
        st, gs = self.req("/api/games?refresh")
        self.assertFalse(any(g["source"] == "emulator" for g in gs))
        self.req("/api/settings", {"compat": {"emulators": True}})
        st, _ = self.req("/api/settings", {"rest_after": 7})
        self.assertEqual(st, 400)
        st, s = self.req("/api/settings", {"rest_after": 10, "overscan": 95})
        self.assertEqual((s["rest_after"], s["overscan"]), (10, 95))
        st, _ = self.req("/api/settings", {"compat": {"nope": True}})
        self.assertEqual(st, 400)
        st, a = self.req("/api/audio", {"volume": 150})
        self.assertEqual(a["volume"], 100)

    def test_anyps5_demo_can_be_enabled_and_launched(self):
        self.assertTrue(self.req("/api/modules")[1]["anyps5"]["installed"])
        self.assertEqual(self.req("/api/settings", {"compat": {"anyps5": True}})[0], 200)
        try:
            titles = [game for game in self.req("/api/games?refresh")[1] if game["source"] == "anyps5"]
            self.assertEqual(len(titles), 1)
            status, running = self.req(f"/api/games/{titles[0]['id']}/launch", {})
            self.assertEqual((status, running["running"]), (200, True))
        finally:
            self.req("/api/running/stop", {})
            self.req("/api/settings", {"compat": {"anyps5": False}})

    def test_users_edit_delete(self):
        st, u = self.req("/api/users", {"name": "Ana", "color": "teal"})
        self.assertEqual(st, 201)
        st, u2 = self.req(f"/api/users/{u['id']}", {"name": "Ana M", "color": "orange"})
        self.assertEqual((u2["name"], u2["color"]), ("Ana M", "orange"))
        st, _ = self.req(f"/api/users/{u['id']}/delete", {})
        self.assertEqual(st, 200)
        st, _ = self.req(f"/api/users/{u['id']}/delete", {})
        self.assertEqual(st, 404)

    def test_demo_wifi_bluetooth_updates(self):
        st, r = self.req("/api/network/connect", {"ssid": "Home Network", "password": "wrongpass1"})
        self.assertEqual(st, 422)
        st, n = self.req("/api/network/connect", {"ssid": "Home Network", "password": "password123"})
        self.assertTrue(next(w for w in n["wifi"] if w["ssid"] == "Home Network")["active"])
        st, n = self.req("/api/network/forget", {"name": "Home Network"})
        self.assertFalse(any(s["name"] == "Home Network" for s in n["saved"]))
        st, b = self.req("/api/bluetooth/scan", {})
        self.assertTrue(b["scanning"])
        st, b = self.req("/api/bluetooth/pair", {"mac": "AA:BB:CC:00:00:02"})
        self.assertTrue(any(d["mac"] == "AA:BB:CC:00:00:02" and d["paired"] for d in b["devices"]))
        st, u = self.req("/api/updates/check", {})
        self.assertEqual(u["available"]["version"], "0.2")
        st, u = self.req("/api/updates/apply", {})
        self.assertEqual(u["staged"]["version"], "0.2")
        st, t = self.req("/api/timedate", {"timezone": "Mars/Base"})
        self.assertEqual(st, 400)
        st, t = self.req("/api/timedate", {"timezone": "Europe/London"})
        self.assertEqual(t["timezone"], "Europe/London")

    def test_power_unknown(self):
        st, _ = self.req("/api/power/selfdestruct", {})
        self.assertEqual(st, 400)


if __name__ == "__main__":
    unittest.main()
