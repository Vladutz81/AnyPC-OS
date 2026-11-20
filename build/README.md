# Building the AnyPC OS image

AnyPC OS is built as a **bootable container** on top of Fedora's `bootc` base
image: the whole OS is one container image, updated atomically, with rollback.

The current build uses Fedora 44 on x86-64. The installer is a pre-alpha build.

## 1. Build the OS image

Use rootful Podman on Linux so the build and the ISO generator share the same
image store. The pinned ISO builder requires an x86-64 CPU with AVX2.

```sh
sudo podman build -f build/Containerfile -t localhost/anypc-os:dev .
```

## 2. Make an installer ISO or a disk image

Uses [bootc-image-builder](https://github.com/osbuild/bootc-image-builder).
The ISO uses `build/installer.toml` to provision a password-locked `player`
account for console autologin. The graphical installer requires you to choose
the target drive. Set your own administrator credentials during installation
when the installer prompts you.

```sh
mkdir -p out
sudo podman run --rm --privileged \
  --security-opt label=disable \
  -v ./build/installer.toml:/config.toml:ro \
  -v ./out:/output \
  -v /var/lib/containers/storage:/var/lib/containers/storage \
  quay.io/centos-bootc/bootc-image-builder@sha256:dab86ee6b46dcade411b37f4e70b07d93b6a06da0dbfec6fe89247a220e0d9f8 \
  --type anaconda-iso --local --rootfs ext4 --chown "$(id -u):$(id -g)" \
  localhost/anypc-os:dev
```

For a preinstalled `qcow2` image, use `--type qcow2` with
`./build/config.toml` mounted at `/config.toml`. Set your own credentials in
that configuration before using a preinstalled image.

The [Installer image workflow](https://github.com/Vladutz81/AnyPC-OS/actions/workflows/image.yml)
builds the ISO on GitHub. Download the `AnyPC-OS-Installer-x86_64` artifact from
a successful run. Unzip it and verify the ISO against the included `SHA256SUMS`
before writing it to a USB drive.

## 3. Try it in a virtual machine

```sh
qemu-system-x86_64 -enable-kvm -m 4096 -smp 4 -cpu host \
  -device virtio-vga-gl -display gtk,gl=on \
  -drive file=out/qcow2/disk.qcow2,if=virtio
```

## What happens at boot

0. The AnyPC boot splash (Plymouth theme in `session/plymouth/`) shows from the
   first seconds; its last frame stays on screen until the shell draws.
1. greetd logs in the `player` account (`session/greetd.toml`).
2. `anypc-session` starts gamescope.
3. Inside it, `anypc-session-inner` starts `anypc-shelld` and opens the shell
   UI in a full-screen browser.
4. Games launched from the shell open on top of it; quitting a game returns to
   the shell. "Switch to desktop" in the power menu leaves the console session.

## Updating a running system

```sh
sudo bootc switch localhost/anypc-os:dev   # first time
sudo bootc upgrade                          # later
sudo bootc rollback                         # go back one version
```

## Boot splash

The theme lives in `session/plymouth/anypc/`. After changing its artwork, run
`scripts/render_splash.py` to regenerate the PNGs. To preview it on a Linux
desktop without rebooting (needs Plymouth with its X11 renderer, e.g. the
`plymouth-x11` package on Debian/Ubuntu):

```sh
sudo cp -r session/plymouth/anypc /usr/share/plymouth/themes/
sudo plymouthd --no-daemon --kernel-command-line="quiet splash plymouth.ignore-serial-consoles plymouth.splash=anypc" &
sudo plymouth --show-splash; sleep 8; sudo plymouth quit
```
