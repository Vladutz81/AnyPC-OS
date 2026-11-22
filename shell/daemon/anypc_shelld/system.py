"""System integration for the shell.

`Backend` talks to the real system through standard tools:
  wpctl (PipeWire audio), nmcli (NetworkManager), bluetoothctl (BlueZ),
  timedatectl / hostnamectl (systemd), bootc (image updates, through
  systemd units), /sys and /proc for hardware.
`DemoBackend` keeps the same interface in memory and touches nothing.
"""

import json
import os
import platform
import re
import shutil
import socket
import subprocess
import threading
import time

from . import OS_NAME, OS_VERSION
from .games import scan_anyps5
from .leonida import Leonida

TIMEOUT = 8
MAC_RE = re.compile(r"^[0-9A-F]{2}(:[0-9A-F]{2}){5}$")
HOSTNAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
MODE_RE = re.compile(r"^(\d{3,5})x(\d{3,5})$")
REAL_FS = {"ext4", "ext3", "xfs", "btrfs", "vfat", "exfat", "ntfs", "ntfs3", "f2fs"}
UPDATE_STATUS = "/run/anypc/update.json"


class SystemError_(Exception):
    """An action failed; the message is shown to the user."""


def run_full(argv, timeout=TIMEOUT, stdin=None):
    """Run a command; return (returncode, stdout, stderr). rc 127 if missing."""
    if not shutil.which(argv[0]):
        return 127, "", f"{argv[0]} not found"
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False, input=stdin)
    except subprocess.TimeoutExpired:
        return 124, "", "timed out"
    except OSError as e:
        return 126, "", str(e)
    return r.returncode, r.stdout, r.stderr


def run(argv, timeout=TIMEOUT):
    rc, out, _ = run_full(argv, timeout)
    return out if rc == 0 else None


def clean_error(err, fallback="The action failed"):
    """Turn tool stderr into one short sentence."""
    for line in (err or "").splitlines():
        line = line.strip()
        if line:
            line = re.sub(r"^(Error|error):\s*", "", line)
            return line[:160]
    return fallback


# -- parsers (pure, unit-tested) ---------------------------------------------

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


def parse_wpctl_sinks(text):
    """Audio sinks from `wpctl status`: [{'id', 'name', 'default'}]."""
    sinks, in_audio, in_sinks = [], False, False
    for line in (text or "").splitlines():
        if line and not line[0].isspace() and not line.startswith(("│", "├", "└")):
            in_audio = line.strip() == "Audio"
            in_sinks = False
            continue
        if not in_audio:
            continue
        stripped = line.strip(" │├└─")
        if stripped.endswith(":"):
            in_sinks = stripped == "Sinks:"
            continue
        if in_sinks:
            m = re.match(r"^\s*[│ ]*\s*(\*)?\s*(\d+)\.\s+(.+?)(\s+\[vol:.*\])?\s*$", line)
            if m:
                sinks.append({"id": int(m.group(2)), "name": m.group(3).strip(), "default": bool(m.group(1))})
    return sinks


def parse_bt_devices(text):
    """`bluetoothctl devices` -> [(mac, name)]."""
    out = []
    for line in (text or "").splitlines():
        m = re.match(r"^Device\s+([0-9A-F:]{17})\s+(.*)$", line.strip())
        if m:
            out.append((m.group(1), m.group(2).strip()))
    return out


def parse_bt_info(text):
    info = {}
    for line in (text or "").splitlines():
        m = re.match(r"^\s*(Name|Alias|Paired|Connected|Trusted|Icon|Battery Percentage):\s*(.*)$", line)
        if m:
            info[m.group(1)] = m.group(2).strip()
    return info


def parse_bootc_status(data):
    """Summarise `bootc status --format=json` for the UI."""
    st = (data or {}).get("status") or {}

    def img(entry):
        if not entry:
            return None
        i = entry.get("image") or {}
        ref = (i.get("image") or {}).get("image")
        return {"version": i.get("version") or (i.get("imageDigest") or "")[:19] or None,
                "digest": i.get("imageDigest"), "image": ref}

    booted = img(st.get("booted"))
    cached = (st.get("booted") or {}).get("cachedUpdate")
    available = None
    if cached and booted and cached.get("imageDigest") != booted.get("digest"):
        available = {"version": cached.get("version") or (cached.get("imageDigest") or "")[:19]}
    return {"booted": booted, "staged": img(st.get("staged")), "rollback": img(st.get("rollback")),
            "available": available}


def parse_session_conf(text):
    conf = {}
    for line in (text or "").splitlines():
        m = re.match(r"^\s*(ANYPC_[A-Z_]+)=([0-9A-Za-z_]*)\s*$", line)
        if m:
            conf[m.group(1)] = m.group(2)
    return conf


# -- the real backend ---------------------------------------------------------

class Backend:
    demo = False

    def __init__(self, config_dir=None):
        self.config_dir = config_dir or os.path.join(
            os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config"), "anypc")
        self._leonida = Leonida(demo=self.demo)
        self._bt_scanning_until = 0
        self._lock = threading.Lock()

    # ---------- hardware info ----------
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
        return {"os": f"{OS_NAME} {OS_VERSION}", "hostname": socket.gethostname(), "kernel": platform.release(),
                "cpu": cpu, "gpus": gpus, "memory": mem_total}

    def set_hostname(self, name):
        if not isinstance(name, str) or not HOSTNAME_RE.match(name):
            raise ValueError("use 1-63 letters, digits or hyphens")
        rc, _, err = run_full(["hostnamectl", "set-hostname", name])
        if rc != 0:
            raise SystemError_(clean_error(err, "Could not change the device name"))
        return {"hostname": name}

    # ---------- storage ----------
    def storage(self):
        seen, out = set(), []
        try:
            with open("/proc/mounts") as f:
                lines = f.read().splitlines()
        except OSError:
            lines = []
        for line in lines:
            parts = line.split()
            if len(parts) < 3:
                continue
            dev, mnt, fs = parts[0], parts[1].replace("\\040", " "), parts[2]
            if not dev.startswith("/dev/") or fs not in REAL_FS or dev in seen:
                continue
            if mnt.startswith(("/boot", "/efi", "/sysroot", "/snap")):
                continue
            try:
                st = os.statvfs(mnt)
            except OSError:
                continue
            seen.add(dev)
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            if total <= 0:
                continue
            removable = mnt.startswith(("/run/media/", "/media/", "/mnt/"))
            out.append({"mount": mnt, "device": dev, "fs": fs, "total": total, "used": total - free,
                        "free": free, "removable": removable})
        out.sort(key=lambda d: (d["removable"], d["mount"]))
        return out

    # ---------- audio ----------
    def audio(self):
        parsed = parse_wpctl_volume(run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"]))
        if not parsed:
            return {"available": False, "volume": None, "muted": False, "outputs": []}
        vol, muted = parsed
        return {"available": True, "volume": vol, "muted": muted,
                "outputs": parse_wpctl_sinks(run(["wpctl", "status"]))}

    def set_audio(self, volume=None, muted=None, output=None):
        if output is not None:
            ids = {s["id"] for s in self.audio().get("outputs", [])}
            if output not in ids:
                raise ValueError("unknown output")
            run(["wpctl", "set-default", str(int(output))])
        if volume is not None:
            v = max(0, min(100, int(volume)))
            run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{v / 100:.2f}"])
        if muted is not None:
            run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if muted else "0"])
        return self.audio()

    # ---------- network ----------
    def network(self, rescan=False):
        out = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"])
        if out is None:
            return {"available": False, "devices": [], "wifi": [], "saved": [], "wifiEnabled": False}
        devices = []
        for line in out.splitlines():
            f = split_nmcli(line)
            if len(f) >= 4 and f[1] in ("ethernet", "wifi"):
                devices.append({"device": f[0], "type": f[1], "state": f[2].split(" ")[0],
                                "connection": f[3] or None})
        radio = (run(["nmcli", "radio", "wifi"]) or "").strip() == "enabled"
        wifi = []
        if radio and any(d["type"] == "wifi" for d in devices):
            cmd = ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"]
            if rescan:
                cmd += ["--rescan", "yes"]
            seen = set()
            for line in (run(cmd, timeout=20) or "").splitlines():
                f = split_nmcli(line)
                if len(f) >= 4 and f[1] and f[1] not in seen:
                    seen.add(f[1])
                    wifi.append({"ssid": f[1], "signal": int(f[2]) if f[2].isdigit() else 0,
                                 "secure": bool(f[3]) and f[3] != "--", "active": f[0] == "*"})
            wifi.sort(key=lambda w: (not w["active"], -w["signal"]))
        saved = []
        for line in (run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"]) or "").splitlines():
            f = split_nmcli(line)
            if len(f) >= 2 and f[1] in ("802-11-wireless", "802-3-ethernet"):
                saved.append({"name": f[0], "type": "wifi" if f[1] == "802-11-wireless" else "ethernet"})
        saved_names = {s["name"] for s in saved}
        for w in wifi:
            w["saved"] = w["ssid"] in saved_names
        return {"available": True, "devices": devices, "wifi": wifi[:20], "saved": saved, "wifiEnabled": radio}

    def wifi_connect(self, ssid, password=None):
        if not isinstance(ssid, str) or not ssid or len(ssid.encode()) > 32 or any(ord(c) < 32 for c in ssid):
            raise ValueError("invalid network name")
        cmd = ["nmcli", "--wait", "30", "device", "wifi", "connect", ssid]
        if password:
            if not isinstance(password, str) or not 8 <= len(password) <= 63:
                raise ValueError("Wi-Fi passwords are 8 to 63 characters")
            cmd += ["password", password]
        rc, _, err = run_full(cmd, timeout=45)
        if rc != 0:
            raise SystemError_(clean_error(err, "Could not connect"))
        return self.network()

    def wifi_radio(self, on):
        rc, _, err = run_full(["nmcli", "radio", "wifi", "on" if on else "off"])
        if rc != 0:
            raise SystemError_(clean_error(err))
        return self.network()

    def net_disconnect(self, device):
        known = {d["device"] for d in self.network()["devices"]}
        if device not in known:
            raise ValueError("unknown device")
        rc, _, err = run_full(["nmcli", "device", "disconnect", device])
        if rc != 0:
            raise SystemError_(clean_error(err))
        return self.network()

    def net_forget(self, name):
        known = {s["name"] for s in self.network()["saved"]}
        if name not in known:
            raise ValueError("unknown connection")
        rc, _, err = run_full(["nmcli", "connection", "delete", "id", name])
        if rc != 0:
            raise SystemError_(clean_error(err))
        return self.network()

    # ---------- bluetooth ----------
    def bluetooth(self):
        show = run(["bluetoothctl", "show"])
        if show is None:
            return {"available": False, "powered": False, "scanning": False, "devices": []}
        powered = bool(re.search(r"Powered:\s*yes", show))
        devices = []
        for mac, name in parse_bt_devices(run(["bluetoothctl", "devices"])):
            i = parse_bt_info(run(["bluetoothctl", "info", mac]))
            batt = re.search(r"\((\d+)\)", i.get("Battery Percentage", ""))
            devices.append({"mac": mac, "name": i.get("Alias") or i.get("Name") or name,
                            "paired": i.get("Paired") == "yes", "connected": i.get("Connected") == "yes",
                            "icon": i.get("Icon", ""), "battery": int(batt.group(1)) if batt else None})
        devices.sort(key=lambda d: (not d["connected"], not d["paired"], d["name"].lower()))
        return {"available": True, "powered": powered, "scanning": time.time() < self._bt_scanning_until,
                "devices": devices[:30]}

    def bt_power(self, on):
        rc, _, err = run_full(["bluetoothctl", "power", "on" if on else "off"])
        if rc != 0:
            raise SystemError_(clean_error(err))
        return self.bluetooth()

    def bt_scan(self, seconds=15):
        with self._lock:
            if time.time() < self._bt_scanning_until:
                return self.bluetooth()
            self._bt_scanning_until = time.time() + seconds
        threading.Thread(target=run_full, args=(["bluetoothctl", "--timeout", str(seconds), "scan", "on"],),
                         kwargs={"timeout": seconds + 5}, daemon=True).start()
        return self.bluetooth()

    def bt_action(self, mac, action):
        if not isinstance(mac, str) or not MAC_RE.match(mac):
            raise ValueError("invalid device address")
        if action == "pair":
            steps = [["bluetoothctl", "--agent=NoInputNoOutput", "pair", mac], ["bluetoothctl", "trust", mac],
                     ["bluetoothctl", "connect", mac]]
        elif action in ("connect", "disconnect", "remove"):
            steps = [["bluetoothctl", action, mac]]
        else:
            raise ValueError("unknown action")
        for cmd in steps:
            rc, out, err = run_full(cmd, timeout=30)
            if rc != 0:
                raise SystemError_(clean_error(err or out, "The device did not respond"))
        return self.bluetooth()

    # ---------- display ----------
    def displays(self):
        outs = []
        base = "/sys/class/drm"
        try:
            names = sorted(os.listdir(base))
        except OSError:
            names = []
        for n in names:
            p = os.path.join(base, n)
            try:
                with open(os.path.join(p, "status")) as f:
                    if f.read().strip() != "connected":
                        continue
                with open(os.path.join(p, "modes")) as f:
                    modes = [m.strip() for m in f.read().splitlines() if MODE_RE.match(m.strip())]
            except OSError:
                continue
            uniq = []
            for m in modes:
                if m not in uniq:
                    uniq.append(m)
            outs.append({"connector": n.split("-", 1)[-1], "modes": uniq})
        conf = self.session_conf()
        cur = "auto"
        if conf.get("ANYPC_WIDTH") and conf.get("ANYPC_HEIGHT"):
            cur = f"{conf['ANYPC_WIDTH']}x{conf['ANYPC_HEIGHT']}"
        return {"outputs": outs, "mode": cur}

    def session_conf_path(self):
        return os.path.join(self.config_dir, "session.conf")

    def session_conf(self):
        try:
            with open(self.session_conf_path()) as f:
                return parse_session_conf(f.read())
        except OSError:
            return {}

    def set_display_mode(self, mode):
        if mode != "auto":
            m = MODE_RE.match(mode or "")
            allowed = {x for o in self.displays()["outputs"] for x in o["modes"]}
            if not m or mode not in allowed:
                raise ValueError("unsupported resolution")
        conf = self.session_conf()
        conf.pop("ANYPC_WIDTH", None)
        conf.pop("ANYPC_HEIGHT", None)
        if mode != "auto":
            w, h = mode.split("x")
            conf["ANYPC_WIDTH"], conf["ANYPC_HEIGHT"] = w, h
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.session_conf_path(), "w") as f:
            f.write("# Written by AnyPC OS settings. Read by anypc-session at start.\n")
            for k, v in sorted(conf.items()):
                f.write(f"{k}={v}\n")
        return self.displays()

    # ---------- date & time ----------
    def timedate(self):
        out = run(["timedatectl", "show"])
        if out is None:
            return {"available": False, "timezone": None, "ntp": None, "synced": None}
        kv = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        return {"available": True, "timezone": kv.get("Timezone"), "ntp": kv.get("NTP") == "yes",
                "synced": kv.get("NTPSynchronized") == "yes"}

    def timezones(self):
        out = run(["timedatectl", "list-timezones"])
        return [z for z in (out or "").splitlines() if z]

    def set_timezone(self, zone):
        if zone not in set(self.timezones()):
            raise ValueError("unknown time zone")
        rc, _, err = run_full(["timedatectl", "set-timezone", zone])
        if rc != 0:
            raise SystemError_(clean_error(err, "Could not change the time zone"))
        return self.timedate()

    def set_ntp(self, on):
        rc, _, err = run_full(["timedatectl", "set-ntp", "true" if on else "false"])
        if rc != 0:
            raise SystemError_(clean_error(err))
        return self.timedate()

    # ---------- updates (bootc via systemd units, see session/systemd) ----------
    def updates(self):
        try:
            with open(UPDATE_STATUS) as f:
                st = json.load(f)
        except (OSError, ValueError):
            st = {}
        managed = shutil.which("bootc") is not None
        summary = parse_bootc_status(st.get("bootc"))
        reported = st.get("available")
        current = summary.get("booted") or {}
        if (isinstance(reported, dict) and isinstance(reported.get("digest"), str)
                and reported["digest"] != current.get("digest")):
            summary["available"] = reported
        return {"managed": managed, "state": st.get("state", "idle"), "error": st.get("error"),
                "checked": st.get("checked"), **summary}

    UPDATE_UNITS = {"check": "anypc-update-check.service", "apply": "anypc-update.service",
                    "rollback": "anypc-rollback.service"}

    def update_action(self, action):
        unit = self.UPDATE_UNITS.get(action)
        if not unit:
            raise ValueError("unknown update action")
        if not shutil.which("bootc"):
            raise SystemError_("This system is not managed by bootc")
        rc, _, err = run_full(["systemctl", "start", "--no-block", unit])
        if rc != 0:
            raise SystemError_(clean_error(err, "Could not start the update service"))
        return {**self.updates(), "state": "working"}

    # ---------- compatibility modules ----------
    def modules(self):
        return {"anyps5": {"installed": os.path.isfile("/usr/libexec/anypc/anyps5/relinker") or bool(scan_anyps5())},
                "leonida": self._leonida.snapshot()}

    def check_leonida(self):
        try:
            self._leonida.start()
        except FileNotFoundError as exc:
            raise SystemError_("The Leonida module is not installed") from exc
        return self.modules()

    # ---------- power ----------
    POWER = {
        "suspend": ["systemctl", "suspend"],
        "reboot": ["systemctl", "reboot"],
        "poweroff": ["systemctl", "poweroff"],
    }

    def _flag(self, value):
        flag = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "anypc-next-session")
        with open(flag, "w") as f:
            f.write(value + "\n")

    def power(self, action):
        if action == "restart-shell":
            self._flag("restart")
            return {"ok": True, "action": action, "note": "exit-shell"}
        argv = self.POWER.get(action)
        if not argv:
            raise ValueError(f"unknown power action: {action}")
        rc, _, err = run_full(argv)
        if rc != 0:
            raise SystemError_(clean_error(err))
        return {"ok": True, "action": action}


# -- demo backend ---------------------------------------------------------------

class DemoBackend(Backend):
    demo = True

    def __init__(self, config_dir=None):
        super().__init__(config_dir)
        self._vol, self._muted, self._out = 70, False, 48
        self._host = "anypc-demo"
        self._tz, self._ntp = "Europe/Bucharest", True
        self._mode = "auto"
        self._wifi_on = True
        self._wifi = [{"ssid": "Home Network", "signal": 82, "secure": True},
                      {"ssid": "Guest", "signal": 55, "secure": False},
                      {"ssid": "Neighbour 5G", "signal": 31, "secure": True}]
        self._active = None
        self._saved = ["Wired connection 1"]
        self._bt_on = True
        self._bt = [{"mac": "AA:BB:CC:00:00:01", "name": "Wireless Controller", "paired": True, "connected": True,
                     "icon": "input-gaming", "battery": 80}]
        self._bt_found = [{"mac": "AA:BB:CC:00:00:02", "name": "Xbox Wireless Controller", "paired": False,
                           "connected": False, "icon": "input-gaming", "battery": None},
                          {"mac": "AA:BB:CC:00:00:03", "name": "Bluetooth Headphones", "paired": False,
                           "connected": False, "icon": "audio-headset", "battery": None}]
        self._update = {"state": "idle", "checked": None, "available": None, "staged": None}

    def info(self):
        return {"os": f"{OS_NAME} {OS_VERSION} (demo)", "hostname": self._host, "kernel": "demo",
                "cpu": "Demo CPU", "gpus": ["Demo GPU"], "memory": 16 * 1024 ** 3}

    def set_hostname(self, name):
        if not isinstance(name, str) or not HOSTNAME_RE.match(name):
            raise ValueError("use 1-63 letters, digits or hyphens")
        self._host = name
        return {"hostname": name}

    def storage(self):
        return [{"mount": "/var", "device": "/dev/nvme0n1p3", "fs": "btrfs", "total": 512 * 1024 ** 3,
                 "used": 180 * 1024 ** 3, "free": 332 * 1024 ** 3, "removable": False},
                {"mount": "/run/media/player/GAMES", "device": "/dev/sda1", "fs": "ext4", "total": 1024 ** 4,
                 "used": 400 * 1024 ** 3, "free": 624 * 1024 ** 3, "removable": True}]

    def audio(self):
        outs = [{"id": 48, "name": "HDMI / DisplayPort", "default": self._out == 48},
                {"id": 52, "name": "Speakers", "default": self._out == 52},
                {"id": 57, "name": "USB Headset", "default": self._out == 57}]
        return {"available": True, "volume": self._vol, "muted": self._muted, "outputs": outs}

    def set_audio(self, volume=None, muted=None, output=None):
        if output is not None:
            if output not in (48, 52, 57):
                raise ValueError("unknown output")
            self._out = output
        if volume is not None:
            self._vol = max(0, min(100, int(volume)))
        if muted is not None:
            self._muted = bool(muted)
        return self.audio()

    def network(self, rescan=False):
        wifi = [dict(w, active=w["ssid"] == self._active, saved=w["ssid"] in self._saved) for w in self._wifi] \
            if self._wifi_on else []
        devices = [{"device": "eth0", "type": "ethernet", "state": "connected", "connection": "Wired connection 1"},
                   {"device": "wlan0", "type": "wifi", "state": "connected" if self._active else "disconnected",
                    "connection": self._active}]
        saved = [{"name": n, "type": "ethernet" if n.startswith("Wired") else "wifi"} for n in self._saved]
        return {"available": True, "devices": devices, "wifi": wifi, "saved": saved, "wifiEnabled": self._wifi_on}

    def wifi_connect(self, ssid, password=None):
        w = next((x for x in self._wifi if x["ssid"] == ssid), None)
        if not w:
            raise ValueError("invalid network name")
        if w["secure"] and ssid not in self._saved:
            if not password or not 8 <= len(password) <= 63:
                raise ValueError("Wi-Fi passwords are 8 to 63 characters")
            if password != "password123":
                raise SystemError_("Secrets were required, but not provided (demo password: password123)")
        self._active = ssid
        if ssid not in self._saved:
            self._saved.append(ssid)
        return self.network()

    def wifi_radio(self, on):
        self._wifi_on = bool(on)
        if not on:
            self._active = None
        return self.network()

    def net_disconnect(self, device):
        if device == "wlan0":
            self._active = None
        elif device != "eth0":
            raise ValueError("unknown device")
        return self.network()

    def net_forget(self, name):
        if name not in self._saved:
            raise ValueError("unknown connection")
        self._saved.remove(name)
        if self._active == name:
            self._active = None
        return self.network()

    def bluetooth(self):
        scanning = time.time() < self._bt_scanning_until
        found = self._bt_found if (scanning or self._bt_scanning_until) else []
        devs = self._bt + [d for d in found if d["mac"] not in {x["mac"] for x in self._bt}]
        return {"available": True, "powered": self._bt_on, "scanning": scanning,
                "devices": [dict(d) for d in devs] if self._bt_on else []}

    def bt_power(self, on):
        self._bt_on = bool(on)
        return self.bluetooth()

    def bt_scan(self, seconds=15):
        self._bt_scanning_until = time.time() + 4
        return self.bluetooth()

    def bt_action(self, mac, action):
        if not isinstance(mac, str) or not MAC_RE.match(mac):
            raise ValueError("invalid device address")
        d = next((x for x in self._bt if x["mac"] == mac), None)
        if action == "pair":
            new = next((x for x in self._bt_found if x["mac"] == mac), None)
            if not new:
                raise SystemError_("The device did not respond")
            self._bt.append(dict(new, paired=True, connected=True))
        elif not d:
            raise ValueError("unknown device")
        elif action == "connect":
            d["connected"] = True
        elif action == "disconnect":
            d["connected"] = False
        elif action == "remove":
            self._bt.remove(d)
        else:
            raise ValueError("unknown action")
        return self.bluetooth()

    def displays(self):
        return {"outputs": [{"connector": "HDMI-A-1", "modes": ["3840x2160", "2560x1440", "1920x1080", "1280x720"]}],
                "mode": self._mode}

    def set_display_mode(self, mode):
        if mode != "auto" and mode not in self.displays()["outputs"][0]["modes"]:
            raise ValueError("unsupported resolution")
        self._mode = mode
        return self.displays()

    def timedate(self):
        return {"available": True, "timezone": self._tz, "ntp": self._ntp, "synced": self._ntp}

    def timezones(self):
        return ["America/New_York", "Asia/Tokyo", "Europe/Berlin", "Europe/Bucharest", "Europe/London",
                "Europe/Madrid", "Europe/Paris", "Europe/Rome", "UTC"]

    def set_timezone(self, zone):
        if zone not in self.timezones():
            raise ValueError("unknown time zone")
        self._tz = zone
        return self.timedate()

    def set_ntp(self, on):
        self._ntp = bool(on)
        return self.timedate()

    def updates(self):
        u = self._update
        return {"managed": True, "state": u["state"], "error": None, "checked": u["checked"],
                "booted": {"version": "0.1", "digest": "sha256:demo", "image": "ghcr.io/vladutz81/anypc-os:latest"},
                "staged": u["staged"], "rollback": None, "available": u["available"]}

    def update_action(self, action):
        if action not in self.UPDATE_UNITS:
            raise ValueError("unknown update action")
        u = self._update
        u["checked"] = int(time.time())
        if action == "check":
            u["available"] = None if u["staged"] else {"version": "0.2"}
        elif action == "apply":
            if not u["available"]:
                raise SystemError_("No update available")
            u["staged"], u["available"] = {"version": "0.2"}, None
        elif action == "rollback":
            raise SystemError_("No previous version on this system")
        return self.updates()

    def modules(self):
        return {"anyps5": {"installed": True}, "leonida": self._leonida.snapshot()}

    def power(self, action):
        if action not in ("suspend", "reboot", "poweroff", "restart-shell"):
            raise ValueError(f"unknown power action: {action}")
        return {"ok": True, "action": action, "demo": True}


DEMO_GAMES = [
    ("SuperTuxKart", "Racing", 24), ("0 A.D.", "Strategy", 42), ("Xonotic", "Shooter", 170),
    ("Veloren", "RPG", 110), ("Luanti", "Sandbox", 265), ("OpenTTD", "Simulation", 345),
    ("Hedgewars", "Strategy", 48), ("Mindustry", "Strategy", 28), ("Endless Sky", "Simulation", 215),
    ("The Battle for Wesnoth", "Strategy", 36), ("RetroArch", "Emulator", 200),
]


def demo_games(compat=None):
    from .games import game_id
    compat = compat or {}
    out = []
    for n, g, h in DEMO_GAMES:
        src = "emulator" if g == "Emulator" else "native"
        if src == "emulator" and not compat.get("emulators", True):
            continue
        if src == "native" and not compat.get("native", True):
            continue
        out.append({"id": game_id("demo", n), "name": n, "genre": g, "source": src,
                    "launch": {"argv": ["true"]}, "art": None, "hue": h})
    if compat.get("anyps5", False):
        out.append({"id": game_id("demo", "Homebrew Sample"), "name": "Homebrew Sample",
                    "genre": "Game", "source": "anyps5", "launch": {"argv": ["true"]},
                    "art": None, "hue": 240})
    return out
