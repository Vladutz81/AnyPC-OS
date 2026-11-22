"""Fixed native module diagnostics and their local HTTP boundary."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from anypc_shelld.leonida import CHECKS, REVISION, Leonida, runtimes
from anypc_shelld.server import App, make_handler, serve
from anypc_shelld.store import Store


class ModuleTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.module = Leonida(self.root)

    def install(self):
        (self.root / "manifest.json").write_text(json.dumps({
            "schema": 1, "revision": REVISION, "kind": "native-diagnostics"}))
        for name, _ in CHECKS:
            binary = self.root / name
            binary.write_text("test fixture")
            binary.chmod(0o755)

    def wait_done(self):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            state = self.module.snapshot()["checks"]
            if state["state"] != "running":
                return state
            time.sleep(.01)
        self.fail("diagnostic worker did not finish")

    def test_missing_or_partial_module_is_unavailable(self):
        self.assertFalse(self.module.snapshot()["installed"])
        with self.assertRaises(FileNotFoundError):
            self.module.start()
        self.install()
        self.assertTrue(self.module.snapshot()["installed"])
        (self.root / CHECKS[0][0]).unlink()
        self.assertFalse(self.module.snapshot()["installed"])

    def test_unrecognized_manifest_is_not_accepted(self):
        self.install()
        for value in ([], {"schema": 1, "revision": "../../tmp",
                           "kind": "native-diagnostics"}, {"schema": 99}):
            (self.root / "manifest.json").write_text(json.dumps(value))
            self.assertFalse(self.module.snapshot()["installed"])

    def test_fixed_commands_run_in_private_scratch_and_report_all_passes(self):
        self.install()
        locations = []
        def execute(argv, **kwargs):
            name = Path(argv[0]).name
            self.assertIn((name, tuple(argv[1:])), CHECKS)
            self.assertEqual(Path(argv[0]).parent, self.root)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stdout"], subprocess.DEVNULL)
            self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
            self.assertLessEqual(kwargs["timeout"], 5)
            self.assertFalse(kwargs.get("shell"))
            locations.append(kwargs["cwd"])
            self.assertTrue(Path(kwargs["cwd"]).is_dir())
            return subprocess.CompletedProcess(argv, 0)
        with patch("anypc_shelld.leonida.subprocess.run", side_effect=execute):
            self.module.start()
            state = self.wait_done()
        self.assertEqual((state["state"], state["passed"], state["failed"]),
                         ("done", len(CHECKS), 0))
        self.assertEqual(len(state["results"]), len(CHECKS))
        self.assertFalse(state["simulated"])
        self.assertIsInstance(state["checked"], int)
        self.assertTrue(locations)
        self.assertTrue(all(not Path(p).exists() for p in locations))
        state["results"].clear()
        self.assertEqual(len(self.module.snapshot()["checks"]["results"]), len(CHECKS))

    def test_failure_and_timeout_are_distinct_from_success(self):
        self.install()
        for result, code in ((subprocess.CompletedProcess([], 1), "failed"),
                             (subprocess.TimeoutExpired([], 5), "timeout"),
                             (OSError("missing dependency"), "unavailable")):
            with self.subTest(error=code):
                args = {"side_effect": result} if isinstance(result, Exception) else {"return_value": result}
                with patch("anypc_shelld.leonida.subprocess.run", **args):
                    self.module.start()
                    state = self.wait_done()
                self.assertEqual(state["state"], "failed")
                self.assertEqual(state["passed"], 0)
                self.assertEqual(state["failed"], len(CHECKS))
                self.assertEqual(state["error"], code)
                self.assertTrue(all(x["error"] == code for x in state["results"]))

    def test_only_one_job_can_run_at_a_time(self):
        self.install()
        entered, release = threading.Event(), threading.Event()
        def execute(argv, **kwargs):
            entered.set()
            release.wait(2)
            return subprocess.CompletedProcess(argv, 0)
        with patch("anypc_shelld.leonida.subprocess.run", side_effect=execute):
            self.module.start()
            self.assertTrue(entered.wait(1))
            try:
                with self.assertRaises(RuntimeError):
                    self.module.start()
            finally:
                release.set()
                self.wait_done()

    def test_overall_time_budget_prevents_further_commands(self):
        self.install()
        with patch("anypc_shelld.leonida.time.monotonic", side_effect=[0] + [31] * len(CHECKS)), \
                patch("anypc_shelld.leonida.subprocess.run") as execute:
            self.module._run()
        execute.assert_not_called()
        state = self.module.snapshot()["checks"]
        self.assertEqual(state["error"], "timeout")
        self.assertEqual(state["failed"], len(CHECKS))

    def test_runtime_detection_covers_flatpak_and_custom_proton(self):
        with patch("anypc_shelld.leonida.shutil.which", return_value=None):
            self.assertEqual(runtimes(self.root), {"wine": False, "proton": False})
            for folder in (".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Proton 10",
                           ".local/share/Steam/compatibilitytools.d/GE-Proton"):
                proton = self.root / folder / "proton"
                proton.parent.mkdir(parents=True)
                proton.write_text("presence fixture")
                self.assertTrue(runtimes(self.root)["proton"])
                proton.unlink()
        with patch("anypc_shelld.leonida.shutil.which", return_value="/usr/bin/wine64"):
            self.assertTrue(runtimes(self.root)["wine"])

    def test_package_manifest_matches_fixed_checks(self):
        manifest = Path(__file__).resolve().parents[3] / "compat/leonida/manifest.json"
        data = json.loads(manifest.read_text())
        self.assertEqual(data["revision"], REVISION)
        self.assertEqual(data["checks"], [name for name, _ in CHECKS])

    def test_demo_never_runs_a_command_or_needs_installed_files(self):
        self.module = Leonida(self.root, demo=True)
        with patch("anypc_shelld.leonida.subprocess.run", side_effect=AssertionError("demo executed a command")):
            self.assertTrue(self.module.snapshot()["installed"])
            self.module.start()
            state = self.wait_done()
        self.assertEqual(state["passed"], len(CHECKS))
        self.assertTrue(state["simulated"])
        self.assertEqual(list(self.root.iterdir()), [])


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.app = App(None, store=Store(os.path.join(self.scratch.name, "state.json")),
                       demo=True, port=0)
        self.server = serve(self.app, "127.0.0.1", 0)
        self.app.port = self.server.server_address[1]
        self.server.RequestHandlerClass = make_handler(self.app)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.close_server)

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()

    def post(self, body, host=None, header="1"):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.app.port}/api/modules/leonida/check",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "X-AnyPC": header,
                     "Host": host or f"127.0.0.1:{self.app.port}"})
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as response:
            with response:
                return response.code, json.loads(response.read())

    def test_module_job_uses_existing_host_and_post_protections(self):
        self.assertEqual(self.post({}, host="evil.example")[0], 403)
        self.assertEqual(self.post({}, header="0")[0], 403)
        self.assertEqual(self.post({"path": "/tmp/untrusted", "args": ["anything"]})[0], 400)
        status, modules = self.post({})
        self.assertEqual(status, 202)
        self.assertTrue(modules["leonida"]["installed"])
        self.assertIn("anyps5", modules)
        self.assertTrue(modules["leonida"]["checks"]["simulated"])
        self.assertEqual(self.post({})[0], 409)
        time.sleep(.3)

    def test_missing_module_returns_a_user_visible_failure(self):
        self.app.backend._leonida = Leonida(Path(self.scratch.name) / "missing")
        self.assertEqual(self.post({})[0], 422)


if __name__ == "__main__":
    unittest.main()
