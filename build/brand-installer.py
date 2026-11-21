#!/usr/bin/env python3
"""Apply AnyPC branding to a bootc-image-builder Anaconda ISO."""

import argparse
import gzip
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


BUILD = Path(__file__).resolve().parent
BRANDING = BUILD / "branding"
VOLUME = "ANYPC_OS"
EFI_PARTITION_TYPE = "28732ac11ff8d211ba4b00a0c93ec93b"
BOOT_THEME = "/boot/grub2/themes/anypc"
BOOT_CONFIGS = {
    "/EFI/BOOT/grub.cfg": "efi.cfg",
    "/boot/grub2/grub.cfg": "bios.cfg",
}
GRUB_STYLE = f"""
set menu_color_normal=white/black
set menu_color_highlight=white/blue
if loadfont /EFI/BOOT/fonts/unicode.pf2; then
  set gfxmode=auto
  insmod gfxterm
  if terminal_output gfxterm; then
    insmod gfxmenu
    set theme={BOOT_THEME}/theme.txt
    export theme
  fi
fi
"""


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def product_archive(product, items):
    archive = run("cpio", "--quiet", "--null", "-o", "-H", "newc", "--owner=0:0",
                  cwd=product, input=b"\0".join(items) + b"\0", stdout=subprocess.PIPE)
    return gzip.compress(archive.stdout, mtime=0)


def install_frontend(stage, root):
    patches = [
        ("usr/share/anaconda/tmux.conf", "new-session -d -s anaconda -n main anaconda",
         'new-session -d -s anaconda -n main "/bin/bash /usr/libexec/anypc-setup/start.sh"'),
        ("usr/bin/anaconda", "    if not conf.system.can_reboot:",
         '    if not conf.system.can_reboot or os.environ.get("ANYPC_INSTALL_KEEP_SESSION") == "1":'),
    ]
    for path, original, replacement in patches:
        source = run("unsquashfs", "-cat", stage, path, stdout=subprocess.PIPE, text=True).stdout
        if source.count(original) != 1:
            raise ValueError(f"Installer runtime changed in {path}. Review its setup entry point.")
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.replace(original, replacement), encoding="utf-8")
        if path.startswith("usr/bin/"):
            target.chmod(0o755)


def brand_grub(config):
    stage2 = re.search(r"inst\.stage2=hd:LABEL=([^\s]+)", config)
    product = re.search(r"(?m)^menuentry 'Install ([^']+)'", config)
    if not stage2 or not product:
        raise ValueError("Unsupported installer menu. Expected an Anaconda install entry and a stage2 label.")

    config = config.replace(stage2[1], VOLUME).replace(product[1], "AnyPC OS")
    config = re.sub(r"Rescue a [^']+ system", "Recover AnyPC OS", config)
    config = re.sub(r"( --class \S+)+(?= \{)", " --class anypc", config)
    config = config.replace("nomodeset", "nomodeset inst.anypc-native")
    config = config.replace("set timeout=60", "set timeout=10")
    quiet_boot = (
        "rd.systemd.show_status=0 systemd.show_status=0 loglevel=0 "
        "rd.udev.log_level=crit rd.systemd.log_level=crit systemd.log_level=crit "
        "logo.nologo vt.global_cursor_default=0 rd.plymouth=0 plymouth.enable=0"
    )
    config = re.sub(
        r"(?m)^(\s*linux\s+(?!.*(?:nomodeset|inst\.rescue)).*\bquiet)$",
        lambda command: f"{command[0]} {quiet_boot}",
        config,
    )
    entry = re.search(r"(?ms)^menuentry 'Install AnyPC OS'[^\n]*\n.*?^}", config)
    if not entry:
        raise ValueError("No standard AnyPC installation entry to localize.")
    english = entry[0].replace("'Install AnyPC OS'", "'Install AnyPC OS (English)'")
    romanian = entry[0].replace("'Install AnyPC OS'", "'Instalează AnyPC OS (română)'")
    romanian = re.sub(r"(?m)^(\s*linux\s+[^\n]+)$", r"\1 inst.lang=ro_RO.UTF-8", romanian)
    config = config[:entry.start()] + romanian + "\n\n" + english + config[entry.end():]
    start = config.index("\nmenuentry ")
    return config[:start] + GRUB_STYLE + config[start:]


def remaster(source, output):
    with tempfile.TemporaryDirectory(prefix="anypc-iso-", dir=output.parent) as work:
        stage = Path(work)
        esp = "/images/efiboot.img"
        initrd = "/images/pxeboot/initrd.img"
        inputs = {**BOOT_CONFIGS, esp: "efiboot.img", initrd: "initrd.img"}
        extract = []
        for path, name in inputs.items():
            extract.extend(("-extract", path, str(stage / name)))
        run("xorriso", "-osirrox", "on", "-indev", source, *extract,
            "-extract", "/images/install.img", stage / "install.img")

        for name in BOOT_CONFIGS.values():
            config = stage / name
            config.write_text(brand_grub(config.read_text(encoding="utf-8")), encoding="utf-8")
        # The FAT image is also appended as a GPT EFI System Partition for USB boot.
        run("mcopy", "-o", "-i", stage / inputs[esp], stage / BOOT_CONFIGS["/EFI/BOOT/grub.cfg"],
            "::/EFI/BOOT/grub.cfg")

        product = stage / "product.img"
        product_root = shutil.copytree(BRANDING / "product", stage / "overlay")
        install_frontend(stage / "install.img", product_root)
        items = sorted(os.fsencode(path.relative_to(product_root)) for path in product_root.rglob("*"))
        product.write_bytes(product_archive(product_root, items))
        # Early dracut looks for this stamp before it has mounted product.img.
        # The kernel accepts consecutive initramfs archives.
        with (stage / inputs[initrd]).open("ab") as image:
            image.write(b"\0" * (-image.tell() % 4))
            image.write(product_archive(product_root, [b".buildstamp"]))
        files = {**{path: stage / name for path, name in inputs.items()},
                 "/images/product.img": product,
                 f"{BOOT_THEME}/theme.txt": BRANDING / "grub-theme.txt",
                 f"{BOOT_THEME}/mark.png": BUILD.parent / "session/plymouth/anypc/mark.png"}
        maps = []
        for path, file in files.items():
            maps.extend(("-map", str(file), path))
        image = stage / "installer.iso"
        run("xorriso", "-indev", source, "-outdev", image, "-volid", VOLUME,
            *maps, "-boot_image", "any", "replay",
            "-append_partition", "2", EFI_PARTITION_TYPE, stage / inputs[esp], "-commit", "-end")
        run("implantisomd5", "--force", "--supported-iso", image)
        run("checkisomd5", image)
        # Link the completed image atomically. An existing destination is an error.
        os.link(image, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_file() or output.exists() or not output.parent.is_dir():
        parser.error("Provide an existing source ISO and a new output ISO in an existing directory.")
    for tool in ("cpio", "unsquashfs", "xorriso", "mcopy", "implantisomd5", "checkisomd5"):
        if not shutil.which(tool):
            parser.error(f"Required tool missing: {tool}")
    remaster(source, output)


if __name__ == "__main__":
    main()
