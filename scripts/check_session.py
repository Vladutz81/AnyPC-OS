"""Regression check for the kiosk browser's per-session profile."""

import json
import os
import socket
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


INNER = Path(__file__).resolve().parents[1] / "session/anypc-session-inner"

BACKEND = """#!/usr/bin/env python3
import os
import signal
import socket
import sys

def stop(*_):
    print("stopped", flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, stop)
signal.alarm(20)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", int(os.environ["ANYPC_PORT"])))
    listener.listen()
    signal.pause()
"""

BROWSER = """#!/usr/bin/env python3
import json
import stat
import sys
from pathlib import Path

directory = Path(next(arg.split("=", 1)[1] for arg in sys.argv[1:]
                      if arg.startswith("--user-data-dir=")))
print(json.dumps({"directory": str(directory), "mode": stat.S_IMODE(directory.stat().st_mode)}))
"""


class KioskSessionTests(unittest.TestCase):
    def test_legacy_browser_lock_survives_and_each_launch_gets_a_private_profile(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            data = root / "data" / "anypc"
            old_browser = data / "browser"
            old_browser.mkdir(parents=True)
            preferences = old_browser / "Preferences"
            preferences.write_text("preserve this profile", encoding="utf-8")
            lock = old_browser / "SingletonLock"
            lock.symlink_to("previous-host-99999")

            backend = root / "anypc-shelld"
            browser = root / "browser"
            for path, code in ((backend, BACKEND), (browser, BROWSER)):
                path.write_text(code, encoding="utf-8")
                path.chmod(0o700)

            env = dict(os.environ, PATH=f"{root}{os.pathsep}{os.environ['PATH']}",
                       XDG_DATA_HOME=str(data.parent), XDG_RUNTIME_DIR=str(runtime),
                       ANYPC_BROWSER=str(browser))
            profiles = set()
            log = data / "shelld.log"
            for run in (1, 2):
                with socket.socket() as probe:
                    probe.bind(("127.0.0.1", 0))
                    env["ANYPC_PORT"] = str(probe.getsockname()[1])
                result = subprocess.run(["bash", str(INNER)], env=env, capture_output=True,
                                        check=True, text=True, timeout=15)
                browser_run = json.loads(result.stdout)
                profile = Path(browser_run["directory"])
                self.assertEqual(profile.parent, runtime)
                self.assertEqual(browser_run["mode"], 0o700)
                self.assertNotIn(profile, profiles)
                self.assertFalse(profile.exists(), "exiting must remove the temporary profile")
                profiles.add(profile)

                # The EXIT trap may send SIGTERM immediately before the shell exits.
                deadline = time.monotonic() + 3
                while log.read_text(encoding="utf-8").splitlines().count("stopped") < run:
                    self.assertLess(time.monotonic(), deadline, "the shell daemon was not stopped")
                    time.sleep(0.025)

                self.assertEqual(preferences.read_text(encoding="utf-8"), "preserve this profile")
                self.assertEqual(os.readlink(lock), "previous-host-99999")


if __name__ == "__main__":
    unittest.main()
