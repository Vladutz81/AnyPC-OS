"""Expose the console display, controllers and per-title data to native exports."""

import os
from pathlib import Path


def command(game):
    executable = Path(game["launch"]["argv"][0])
    folder = executable.parent
    save = Path.home() / ".local/share/anypc/titles" / game["id"]
    save.mkdir(parents=True, exist_ok=True, mode=0o700)
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    args = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session", "--clearenv",
            "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib64", "/lib64",
            "--symlink", "usr/lib", "/lib", "--symlink", "usr/bin", "/bin",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--ro-bind", "/sys", "/sys",
            "--dev-bind-try", "/dev/dri", "/dev/dri",
            "--dev-bind-try", "/dev/snd", "/dev/snd", "--dir", "/dev/shm",
            "--dir", "/run/console", "--setenv", "XDG_RUNTIME_DIR", "/run/console",
            "--setenv", "LANG", os.environ.get("LANG", "C.UTF-8"), "--setenv", "PATH", "/usr/bin",
            "--setenv", "HOME", "/home/player", "--bind", str(save), "/home/player",
            "--ro-bind", str(folder), "/game", "--chdir", "/game"]
    for device in Path("/dev/input").glob("*"):
        if not device.is_char_device():
            continue
        dev = device.stat().st_rdev
        try:
            info = Path(f"/run/udev/data/c{os.major(dev)}:{os.minor(dev)}").read_text()
        except OSError:
            continue
        if "E:ID_INPUT_JOYSTICK=1" in info.splitlines():
            args += ["--dev-bind-try", str(device), str(device)]
    for name in ("ld.so.cache", "fonts", "vulkan", "drirc", "machine-id", "localtime"):
        args += ["--ro-bind-try", "/etc/" + name, "/etc/" + name]
    for name in ("pulse", "pipewire-0"):
        args += ["--bind-try", str(runtime / name), "/run/console/" + name]
    wayland = os.environ.get("WAYLAND_DISPLAY", "")
    if wayland and "/" not in wayland:
        args += ["--bind-try", str(runtime / wayland), "/run/console/" + wayland,
                 "--setenv", "WAYLAND_DISPLAY", wayland]
    if os.environ.get("DISPLAY"):
        args += ["--ro-bind-try", "/tmp/.X11-unix", "/tmp/.X11-unix",
                 "--setenv", "DISPLAY", os.environ["DISPLAY"]]
    if os.environ.get("XAUTHORITY"):
        args += ["--ro-bind-try", os.environ["XAUTHORITY"], "/run/console/Xauthority",
                 "--setenv", "XAUTHORITY", "/run/console/Xauthority"]
    return args + ["/game/" + executable.name]
