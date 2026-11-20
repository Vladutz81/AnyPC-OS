"""System integration: hardware info, audio, network, power.

Everything goes through `Backend`; `DemoBackend` fakes it for development
and previews so nothing on the host is touched.
"""

import os
import platform
import re
import shutil
import subprocess

from . import OS_NAME, OS_VERSION

TIMEOUT = 5


def run(argv, timeout=TIMEOUT):
    """Run a command; return stdout text or None if it is missing or fails."""
    if not shutil.which(argv[0]):
        return None
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def split_nmcli(line):
    """Split one line of `nmcli -t` output (':' separated, '\\:' escaped)."""
    out, cur, esc = [], [], False
    for ch in line:
        if esc:
            cur.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    out.append("".join(cur))
    return out


def parse_wpctl_volume(text):
    """'Volume: 0.45 [MUTED]' -> (45, True)."""
    m = re.search(r"Volume:\s*([0-9.]+)", text or "")
    if not m:
        return None
    return round(float(m.group(1)) * 100), "MUTED" in text


class Backend:
    demo = False

    def info(self):
        mem_total = None
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_total = int(line.split()[1]) * 1024
                        break
        except OSError:
            pass
        cpu = None
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu = line.split(":", 1)[1].strip()
                        break
        except OSError:
            pass
        gpus = []
        out = run(["lspci"])
        if out:
            for line in out.splitlines():
                if re.search(r"VGA compatible controller|3D controller|Display controller", line):
                    gpus.append(line.split(": ", 1)[-1].strip())
        try:
            du = shutil.disk_usage(os.path.expanduser("~"))
            disk = {"total": du.total, "used": du.used}
        except OSError:
            disk = None
        return {
            "os": f"{OS_NAME} {OS_VERSION}",
            "hostname": platform.node(),
            "kernel": platform.release(),
            "cpu": cpu,
            "gpus": gpus,
            "memory": mem_total,
            "disk": disk,
        }

    # -- audio (PipeWire / WirePlumber) -------------------------------------
    def audio(self):
        parsed = parse_wpctl_volume(run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]))
        if not parsed:
            return {"available": False, "volume": None, "muted": False}
        vol, muted = parsed
        return {"available": True, "volume": vol, "muted": muted}

    def set_audio(self, volume=None, muted=None):
        if volume is not None:
            v = max(0, min(100, int(volume)))
            run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{v / 100:.2f}"])
        if muted is not None:
            run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if muted else "0"])
        return self.audio()

    # -- network (NetworkManager) -------------------------------------------
    def network(self):
        out = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"])
        if out is None:
            return {"available": False, "devices": [], "wifi": []}
        devices = []
        for line in out.splitlines():
            f = split_nmcli(line)
            if len(f) >= 4 and f[1] in ("ethernet", "wifi"):
                devices.append({"device": f[0], "type": f[1], "state": f[2], "connection": f[3] or None})
        wifi = []
        wout = run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"]) or ""
        seen = set()
        for line in wout.splitlines():
            f = split_nmcli(line)
            if len(f) >= 4 and f[1] and f[1] not in seen:
                seen.add(f[1])
                wifi.append({"ssid": f[1], "signal": int(f[2]) if f[2].isdigit() else 0,
                             "secure": bool(f[3]) and f[3] != "--", "active": f[0] == "*"})
        wifi.sort(key=lambda w: (not w["active"], -w["signal"]))
        return {"available": True, "devices": devices, "wifi": wifi[:12]}

    # -- power ----------------------------------------------------------------
    POWER = {
        "suspend": ["systemctl", "suspend"],
        "reboot": ["systemctl", "reboot"],
        "poweroff": ["systemctl", "poweroff"],
    }

    def power(self, action):
        if action == "desktop":
            # The session script reads this flag and starts the desktop session next.
            flag = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "anypc-next-session")
            with open(flag, "w") as f:
                f.write("desktop\n")
            return {"ok": True, "action": action, "note": "exit-shell"}
        argv = self.POWER.get(action)
        if not argv:
            raise ValueError(f"unknown power action: {action}")
        ok = run(argv) is not None
        return {"ok": ok, "action": action}


class DemoBackend(Backend):
    demo = True

    def __init__(self):
        self._vol, self._muted = 70, False

    def info(self):
        return {"os": f"{OS_NAME} {OS_VERSION} (demo)", "hostname": "anypc-demo", "kernel": "demo",
                "cpu": "Demo CPU", "gpus": ["Demo GPU"], "memory": 16 * 1024 ** 3,
                "disk": {"total": 512 * 1024 ** 3, "used": 180 * 1024 ** 3}}

    def audio(self):
        return {"available": True, "volume": self._vol, "muted": self._muted}

    def set_audio(self, volume=None, muted=None):
        if volume is not None:
            self._vol = max(0, min(100, int(volume)))
        if muted is not None:
            self._muted = bool(muted)
        return self.audio()

    def network(self):
        return {"available": True,
                "devices": [{"device": "eth0", "type": "ethernet", "state": "connected", "connection": "Wired"}],
                "wifi": [{"ssid": "Demo network", "signal": 78, "secure": True, "active": False}]}

    def power(self, action):
        if action not in ("suspend", "reboot", "poweroff", "desktop"):
            raise ValueError(f"unknown power action: {action}")
        return {"ok": True, "action": action, "demo": True}


DEMO_GAMES = [
    ("SuperTuxKart", "Racing", 24), ("0 A.D.", "Strategy", 42), ("Xonotic", "Shooter", 170),
    ("Veloren", "RPG", 110), ("Luanti", "Sandbox", 265), ("OpenTTD", "Simulation", 345),
    ("Hedgewars", "Strategy", 48), ("Mindustry", "Strategy", 28), ("Endless Sky", "Simulation", 215),
    ("The Battle for Wesnoth", "Strategy", 36),
]


def demo_games():
    from .games import game_id
    return [{"id": game_id("demo", n), "name": n, "genre": g, "source": "native",
             "launch": {"argv": ["true"]}, "art": None, "hue": h} for n, g, h in DEMO_GAMES]
