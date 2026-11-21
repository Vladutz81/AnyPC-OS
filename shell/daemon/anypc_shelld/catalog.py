"""AnyPC-curated applications. All operations run as the current console user."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path

APPS = {"steam": ("Steam", "com.valvesoftware.Steam", "store_steam"),
        "kart": ("SuperTuxKart", "net.supertuxkart.SuperTuxKart", "store_kart"),
        "vlc": ("VLC", "org.videolan.VLC", "store_vlc"),
        "retroarch": ("RetroArch", "org.libretro.RetroArch", "store_engine"),
        "pcsx2": ("PCSX2", "net.pcsx2.PCSX2", "store_engine"),
        "rpcs3": ("RPCS3", "net.rpcs3.RPCS3", "store_engine"),
        "xemu": ("xemu", "app.xemu.xemu", "store_engine"),
        "ppsspp": ("PPSSPP", "org.ppsspp.PPSSPP", "store_engine"),
        "dolphin": ("Dolphin", "org.DolphinEmu.dolphin-emu", "store_engine"),
        "cemu": ("Cemu", "info.cemu.Cemu", "store_engine"),
        "melonds": ("melonDS", "net.kuribo64.melonDS", "store_engine"),
        "mgba": ("mGBA", "io.mgba.mGBA", "store_engine"),
        "flycast": ("Flycast", "org.flycast.Flycast", "store_engine"),
        "mame": ("MAME", "org.mamedev.MAME", "store_engine"),
        "dosbox": ("DOSBox Staging", "io.github.dosbox-staging", "store_engine"),
        "heroic": ("Heroic Games Launcher", "com.heroicgameslauncher.hgl", "store_tool"),
        "moonlight": ("Moonlight", "com.moonlight_stream.Moonlight", "store_tool"),
        "protonup": ("ProtonUp-Qt", "net.davidotek.pupgui2", "store_tool"),
        }
RUNTIME = Path("/usr/libexec/anypc/anyps5")
REPO = "/usr/share/anypc/apps.flatpakrepo"


def imports():
    roots = [Path.home() / "Games" / "Import"]
    media = Path("/run/media") / os.environ.get("USER", "player")
    if media.is_dir():
        roots.extend(p / "AnyPS5" for p in media.iterdir() if p.is_mount())
    result = {}
    for root in roots:
        if not root.is_dir() or root.is_symlink():
            continue
        for directory in sorted(root.iterdir()):
            file = next((directory / name for name in ("eboot.elf", "eboot.bin")
                         if (directory / name).is_file()), None)
            if file is None:
                continue
            if file.is_symlink() or file.parent.is_symlink() or not file.is_file():
                continue
            try:
                with file.open("rb") as stream:
                    if stream.read(4) != b"\x7fELF":
                        continue
            except OSError:
                continue
            key = hashlib.sha256(os.fsencode(file)).hexdigest()[:24]
            result[key] = file
    return result


def convert(file, key):
    destination = Path.home() / "Games/AnyPS5"
    destination.mkdir(parents=True, exist_ok=True)
    final = destination / ("import-" + key)
    if final.exists():
        raise ValueError("already_imported")
    with tempfile.TemporaryDirectory(dir=destination, prefix=".import-") as scratch:
        out = Path(scratch, "result")
        out.mkdir()
        # Expose only the source folder, runtime and temporary output to the converter.
        has_modules = any(file.parent.glob("sce_module/*.prx"))
        options = [] if has_modules else ["--skip-sce-module"]
        subprocess.run(["bwrap", "--unshare-all", "--die-with-parent", "--new-session",
                        "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib64", "/lib64",
                        "--symlink", "usr/lib", "/lib", "--proc", "/proc", "--dev", "/dev",
                        "--tmpfs", "/tmp", "--ro-bind", str(file.parent), "/source",
                        "--bind", str(out), "/output", "--chdir", "/output",
                        str(RUNTIME / "relinker"), *options, "--rpath", str(RUNTIME / "libs"),
                        "/source/" + file.name, "/output/app.elf"], check=True, timeout=600,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in out.rglob("*")):
            raise ValueError("conversion_failed")
        exe = out / "app.elf"
        if exe.is_symlink() or not exe.is_file():
            raise ValueError("conversion_failed")
        exe.chmod(0o755)
        # Copy game-owned content without following links out of the import directory.
        data = out / "app0"
        for base, dirs, files in os.walk(file.parent, followlinks=False):
            base = Path(base)
            dirs[:] = [d for d in dirs if not (base / d).is_symlink()]
            target = data / base.relative_to(file.parent)
            target.mkdir(parents=True, exist_ok=True)
            for name in files:
                src = base / name
                if not src.is_symlink() and src.is_file() and not (target / name).exists():
                    shutil.copyfile(src, target / name)
        name = " ".join(file.parent.name.splitlines())[:100]
        (out / "app.elf.desktop").write_text(
            f"[Desktop Entry]\nType=Application\nName={name}\nExec=app.elf\nCategories=Game;\n",
            encoding="utf-8")
        out.rename(final)


def mount_import_media():
    result = subprocess.run(["lsblk", "--json", "--tree", "--output",
                             "NAME,PATH,TYPE,RM,TRAN,FSTYPE,MOUNTPOINTS"],
                            capture_output=True, text=True, check=True, timeout=10)
    for device in json.loads(result.stdout)["blockdevices"]:
        if device.get("type") != "disk" or not (device.get("rm") or device.get("tran") == "usb"):
            continue
        for node in device.get("children") or [device]:
            if node.get("type") not in ("part", "disk") or any(node.get("mountpoints") or []):
                continue
            if node.get("fstype") not in ("vfat", "exfat", "ntfs", "ext4", "iso9660"):
                continue
            subprocess.run(["udisksctl", "mount", "--no-user-interaction", "--block-device",
                            node["path"], "--options", "ro,nodev,nosuid,noexec"], check=True, timeout=30)


class Catalog:
    def __init__(self, demo=False):
        self.demo = demo
        self.demo_installed = set()
        self.lock = threading.Lock()
        self.job = {"state": "idle"}

    def snapshot(self):
        if self.demo:
            installed = set(self.demo_installed)
            sources = {}
        else:
            installed = set()
            if shutil.which("flatpak"):
                try:
                    result = subprocess.run(["flatpak", "list", "--user", "--app", "--columns=application"],
                                            capture_output=True, text=True, timeout=8)
                    installed.update(result.stdout.splitlines())
                except (OSError, subprocess.TimeoutExpired):
                    pass
            sources = imports()
        with self.lock:
            job = dict(self.job)
        return {"items": [{"id": key, "name": name, "description": desc, "installed": app in installed}
                          for key, (name, app, desc) in APPS.items()],
                "imports": [{"id": key, "name": path.parent.name} for key, path in sources.items()],
                "job": job}

    def start(self, key, action):
        file = None
        if action == "scan" and key == "usb":
            pass
        elif action == "import":
            file = imports().get(key) if isinstance(key, str) and not self.demo else None
            if file is None:
                raise ValueError("unknown_import")
        elif not isinstance(key, str) or key not in APPS or action not in ("install", "open", "update"):
            raise ValueError("unknown_catalog_action")
        with self.lock:
            if self.job["state"] == "working":
                raise RuntimeError("store_busy")
            self.job = {"state": "working", "id": key, "action": action}
        if self.demo:
            if key in APPS:
                self.demo_installed.add(APPS[key][1])
            self._finish("done")
        else:
            threading.Thread(target=self._work, args=(key, action, file), daemon=True).start()
        return {"accepted": True}

    def _finish(self, state):
        with self.lock:
            self.job = {**self.job, "state": state}

    def _work(self, key, action, file):
        try:
            if action == "scan":
                mount_import_media()
            elif action == "import":
                convert(file, key)
            else:
                app = APPS[key][1]
                if action == "open":
                    args = ["flatpak", "run", app] + (["steam://store"] if key == "steam" else [])
                    subprocess.run(["flatpak", "info", "--user", app], check=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
                else:
                    if action == "install":
                        subprocess.run(["flatpak", "remote-add", "--user", "--if-not-exists",
                                        "anypc-apps", REPO], check=True, timeout=120)
                    args = ["flatpak", action, "--user", "--noninteractive", "-y"]
                    if action == "install":
                        args += ["anypc-apps"]
                    subprocess.run(args + [app], check=True, timeout=3600)
        except (OSError, ValueError, subprocess.SubprocessError):
            self._finish("failed")
        else:
            self._finish("done")
