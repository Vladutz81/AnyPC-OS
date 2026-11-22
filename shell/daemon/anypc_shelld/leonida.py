"""Pinned native Leonida diagnostics; never a generic command runner."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time

REVISION = "067d3e8b97189fcf272dc699fdbb871eae496660"
CHECKS = (
    ("pipeline_cache_file_test", ()),
    ("xdxr_descs_test", ()),
    ("command_list_test", ()),
    ("resource_tiling_test", ()),
    ("descriptor_table_test", ()),
    ("typeless_rtv_test", ()),
    ("pipeline_cache_snapshot_test", ()),
    ("clear_color_test", ()),
    ("d3d12_state_map_test", ()),
    ("gfx10_descriptors_test", ()),
    ("vk_descriptor_bench", ("--self-test",)),
)


def runtimes(home=None):
    """Report presence only; neither Wine nor a game is started."""
    home = Path(home) if home is not None else Path.home()
    roots = (home / ".local/share/Steam", home / ".steam/root", home / ".steam/steam",
             home / ".var/app/com.valvesoftware.Steam/.local/share/Steam")
    proton = False
    for root in roots:
        for parent in (root / "steamapps/common", root / "compatibilitytools.d"):
            try:
                if any((entry / "proton").is_file() for entry in parent.iterdir()):
                    proton = True
            except OSError:
                continue
    return {"wine": bool(shutil.which("wine") or shutil.which("wine64")), "proton": proton}


class Leonida:
    def __init__(self, directory="/usr/libexec/anypc/leonida", demo=False):
        self.directory = Path(directory)
        self.demo = demo
        self._lock = threading.Lock()
        self._checks = self._state("idle")

    def _state(self, state):
        return {"state": state, "passed": 0, "failed": 0, "total": len(CHECKS),
                "error": None, "checked": None, "results": [], "simulated": self.demo}

    def _installed(self):
        if self.demo:
            return True
        try:
            with (self.directory / "manifest.json").open(encoding="utf-8") as stream:
                data = json.load(stream)
            return (isinstance(data, dict) and data.get("schema") == 1
                    and data.get("kind") == "native-diagnostics" and data.get("revision") == REVISION
                    and all((self.directory / name).is_file()
                            and os.access(self.directory / name, os.X_OK) for name, _ in CHECKS))
        except (OSError, ValueError):
            return False

    def snapshot(self):
        installed = self._installed()
        with self._lock:
            checks = deepcopy(self._checks)
        return {"installed": installed, "version": REVISION[:12] if installed else None,
                "status": "experimental", **({"wine": True, "proton": True} if self.demo else runtimes()),
                "checks": checks}

    def start(self):
        if not self._installed():
            raise FileNotFoundError("Leonida native diagnostics are not installed")
        with self._lock:
            if self._checks["state"] == "running":
                raise RuntimeError("A module check is already running")
            self._checks = self._state("running")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        if self.demo:
            time.sleep(.2)
            self._finish([{"name": name, "passed": True, "error": None} for name, _ in CHECKS])
            return
        results = []
        try:
            with tempfile.TemporaryDirectory(prefix="anypc-leonida-") as scratch:
                deadline = time.monotonic() + 30
                for name, args in CHECKS:
                    error = None
                    try:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise subprocess.TimeoutExpired(name, 0)
                        proc = subprocess.run([str(self.directory / name), *args], cwd=scratch,
                                              timeout=min(5, remaining), check=False,
                                              stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                              stderr=subprocess.DEVNULL)
                        if proc.returncode != 0:
                            error = "failed"
                    except subprocess.TimeoutExpired:
                        error = "timeout"
                    except OSError:
                        error = "unavailable"
                    results.append({"name": name, "passed": error is None, "error": error})
        except OSError:
            results = [{"name": name, "passed": False, "error": "unavailable"} for name, _ in CHECKS]
        self._finish(results)

    def _finish(self, results):
        failed = sum(not item["passed"] for item in results)
        with self._lock:
            self._checks.update(state="failed" if failed else "done",
                                passed=len(results) - failed, failed=failed, results=results,
                                error=next((item["error"] for item in results if item["error"]), None),
                                checked=int(time.time()))
