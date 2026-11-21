"""Validate a local install plan and run the media's offline installer backend."""

import base64
import fcntl
import json
import os
import re
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path


RUN_DIR = Path("/run/anypc-setup")
PAYLOAD = Path("/run/install/repo/container")
MEDIA_KICKSTART = Path("/run/install/repo/osbuild-base.ks")
COMPLETED = RUN_DIR / "completed"
DISK_NAME = re.compile(r"(?:[svh]d[a-z]+|nvme[0-9]+n[0-9]+|mmcblk[0-9]+)\Z")
LOCALES = {"en": "en_US.UTF-8", "ro": "ro_RO.UTF-8",
           "en_US.UTF-8": "en_US.UTF-8", "ro_RO.UTF-8": "ro_RO.UTF-8"}
KEYBOARDS = {"us", "ro", "gb", "de", "fr"}
TIMEZONES = {"UTC", "Europe/Bucharest", "Europe/London", "Europe/Berlin", "Europe/Paris"}
MIB = 1024 * 1024
MIN_ROOT_MIB = 16 * 1024


@dataclass(frozen=True)
class Disk:
    path: str
    model: str
    size: int
    serial: str
    number: str
    wwn: str
    sequence: str


@dataclass(frozen=True)
class Plan:
    disk: Disk
    mode: str
    boot_mib: int
    swap_mib: int
    profile: str
    locale: str
    timezone: str
    keyboard: str


def occupied(node):
    """Exclude disks carrying any mounted filesystem, install media or active storage stack."""
    if node.get("fstype") == "iso9660" or node.get("label") == "ANYPC_OS":
        return True
    if any(node.get("mountpoints") or ()) or node.get("type") not in ("disk", "part"):
        return True
    return any(occupied(child) for child in node.get("children", ()))


def discover_disks():
    try:
        output = subprocess.check_output(
            ["lsblk", "--json", "--tree", "--bytes", "--output",
             "NAME,PATH,TYPE,SIZE,RO,MODEL,SERIAL,WWN,MAJ:MIN,FSTYPE,LABEL,MOUNTPOINTS"],
            text=True,
        )
        devices = json.loads(output)["blockdevices"]
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        raise RuntimeError("Could not read the available disks.") from error
    disks = []
    for device in devices:
        name = device.get("name") or ""
        path = device.get("path") or ""
        if (device.get("type") != "disk" or device.get("ro") or path != f"/dev/{name}"
                or not DISK_NAME.fullmatch(name) or occupied(device)):
            continue
        size = device.get("size") or 0
        number = device.get("maj:min") or ""
        if size >= (MIN_ROOT_MIB + 768) * MIB and number:
            try:
                sequence = Path("/sys/class/block", name, "diskseq").read_text().strip()
            except OSError:
                continue
            disks.append(Disk(path, (device.get("model") or "").strip(), size,
                              (device.get("serial") or "").strip(), number, device.get("wwn") or "", sequence))
    return disks


def validate_plan(disk, mode, boot_mib, swap_mib, profile, locale, timezone, keyboard):
    if not isinstance(disk, Disk) or mode not in ("automatic", "custom"):
        raise ValueError("Choose a disk and a partition layout.")
    if mode == "automatic":
        boot_mib, swap_mib = 1024, 0
    if not 1024 <= boot_mib <= 8192 or not 0 <= swap_mib <= 65536:
        raise ValueError("The partition sizes are outside the supported range.")
    if disk.size < (MIN_ROOT_MIB + boot_mib + swap_mib + 640) * MIB:
        raise ValueError("Leave at least 16 GiB for the system partition.")
    profile = unicodedata.normalize("NFC", profile).strip()
    if not 1 <= len(profile) <= 16 or any(unicodedata.category(c).startswith("C") for c in profile):
        raise ValueError("Choose a display name of 1–16 characters.")
    if locale not in LOCALES or timezone not in TIMEZONES or keyboard not in KEYBOARDS:
        raise ValueError("Choose a supported language, time zone and keyboard.")
    return Plan(disk, mode, boot_mib, swap_mib, profile, LOCALES[locale], timezone, keyboard)


def kickstart(plan, uefi):
    """Describe an install restricted to one disk; Anaconda performs the writes."""
    name = Path(plan.disk.path).name
    if not DISK_NAME.fullmatch(name):
        raise ValueError("The selected disk is invalid.")
    seed = json.dumps({"profile": plan.profile, "language": plan.locale[:2]}, ensure_ascii=False)
    encoded_seed = base64.b64encode(seed.encode("utf-8")).decode("ascii")
    lines = [
        "graphical",
        "xconfig --startxonboot",
        "reboot",
        f"lang {plan.locale}",
        f"keyboard --vckeymap={plan.keyboard} --xlayouts={plan.keyboard}",
        f"timezone {plan.timezone} --utc",
        "network --hostname=anypc",
        "rootpw --lock --iscrypted *",
        "firstboot --disable",
        f"ignoredisk --only-use={name}",
        f"clearpart --all --initlabel --disklabel=gpt --drives={name}",
        f'bootloader --boot-drive={name} --append="rhgb quiet logo.nologo systemd.show_status=false rd.systemd.show_status=false vt.global_cursor_default=0"',
        f"%include {MEDIA_KICKSTART}",
    ]
    if plan.mode == "automatic":
        lines.append("autopart --type=plain --fstype=ext4 --nohome --noswap")
    else:
        if uefi:
            lines.append(f"part /boot/efi --fstype=efi --size=600 --ondisk={name}")
        else:
            lines.append(f"part biosboot --fstype=biosboot --size=1 --ondisk={name}")
        lines.append(f"part /boot --fstype=ext4 --size={plan.boot_mib} --ondisk={name}")
        if plan.swap_mib:
            lines.append(f"part swap --fstype=swap --size={plan.swap_mib} --ondisk={name}")
        lines.append(f"part / --fstype=ext4 --size={MIN_ROOT_MIB} --grow --ondisk={name}")
    lines.extend((
        "%post --erroronfail",
        "set -eu",
        "umask 022",
        "mkdir -p /etc/anypc",
        f"printf '%s' '{encoded_seed}' | base64 -d > /etc/anypc/initial-profile.json",
        "%end",
        "%post --nochroot --erroronfail",
        f"touch {COMPLETED}",
        "%end",
    ))
    return "\n".join(lines) + "\n"


def run_install(plan, on_phase):
    on_phase("preparing")
    RUN_DIR.mkdir(mode=0o700, exist_ok=True)
    if not PAYLOAD.exists() or not MEDIA_KICKSTART.is_file():
        raise RuntimeError("The offline system image is missing from the boot media.")
    with (RUN_DIR / "install.lock").open("wb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("An installation is already in progress.") from error
        _deploy(plan, on_phase)


def _deploy(plan, on_phase):
    config = kickstart(plan, Path("/sys/firmware/efi").is_dir())
    with tempfile.TemporaryDirectory(dir=RUN_DIR) as directory:
        ks = Path(directory, "install.ks")
        ks.write_text(config, encoding="utf-8")
        ks.chmod(0o600)
        # Re-read the current disk inventory immediately before doing any writes.
        if plan.disk not in discover_disks():
            raise ValueError("The selected disk changed. Return to disk selection and check it again.")
        COMPLETED.unlink(missing_ok=True)
        with (RUN_DIR / "install.log").open("w", encoding="utf-8") as log:
            log_path = Path(log.name)
            log_path.chmod(0o600)
            env = dict(os.environ, LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8",
                       PYTHONUNBUFFERED="1", ANYPC_INSTALL_KEEP_SESSION="1",
                       WAYLAND_DISPLAY="anypc-headless", DISPLAY="")
            on_phase("partitioning")
            with subprocess.Popen(
                ["/usr/bin/anaconda", "--cmdline", "--nosave=all_ks", "--kickstart", str(ks)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, errors="replace", env=env,
            ) as process:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    if "Deployment" in line or "Installing" in line or "ostree" in line.lower():
                        on_phase("installing")
                    elif "Finalizing" in line or "Configuring" in line or "boot loader" in line:
                        on_phase("finishing")
                if process.wait() != 0 or not COMPLETED.exists():
                    raise RuntimeError("Installation stopped. See /run/anypc-setup/install.log for details.")


def reboot():
    subprocess.run(["systemctl", "reboot"], check=True)
