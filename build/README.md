# Building the AnyPC OS image

AnyPC OS is built as a **bootable container** on top of Fedora's `bootc` base
image: the whole OS is one container image, updated atomically, with rollback.

The current build uses Fedora 44 on x86-64. The AnyPC installer is a pre-alpha build.

## 1. Build the OS image

Use rootful Podman on Linux so the build and the ISO generator share the same
image store. The pinned ISO builder requires an x86-64 CPU with AVX2.

```sh
sudo podman build -f build/Containerfile -t anypc.cubx-romania.ro/anypc-os:stable .
```

## 2. Make an installer ISO or a disk image

Uses [bootc-image-builder](https://github.com/osbuild/bootc-image-builder).
The graphical installer asks for a destination and a local AnyPC display name.
The installed OS provisions its password-locked console service account on first
boot and opens the profile directly.

```sh
mkdir -p out
sudo podman run --rm --privileged \
  --security-opt label=disable \
  -v ./build/installer.toml:/config.toml:ro \
  -v ./out:/output \
  -v /var/lib/containers/storage:/var/lib/containers/storage \
  quay.io/centos-bootc/bootc-image-builder@sha256:dab86ee6b46dcade411b37f4e70b07d93b6a06da0dbfec6fe89247a220e0d9f8 \
  --type anaconda-iso --rootfs ext4 --chown "$(id -u):$(id -g)" \
  anypc.cubx-romania.ro/anypc-os:stable
```

Apply the AnyPC OS boot menu, installer theme and product name before distributing
the ISO. Install `cpio`, `xorriso`, `mtools`, `squashfs-tools`, and `isomd5sum` on the build host.
Use the `install.iso` produced in the `out` tree as the first argument:

```sh
python3 build/brand-installer.py out/bootiso/install.iso out/AnyPC-OS-Installer-x86_64.iso
```

The branding step updates both GRUB menus and the boot configuration in the EFI
partition, adds the installer product overlay and verifies the media checksum.
The default boot opens AnyPC Setup in Romanian. English is available in the menu
and in the wizard. Select a dedicated disk, choose automatic partitioning or size
the boot and swap partitions, then create the AnyPC profile. Review the
drive model, device and capacity before confirming erasure of the entire selected
drive. The offline installation engine deploys the embedded system. Setup displays
progress and waits for an explicit restart. Recovery is available from the boot menu.
The machine's firmware controls its own screen before booting the installer.

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

1. greetd logs in the `player` account (`session/greetd.toml`).
2. `anypc-session` starts Gamescope. If it cannot start, Cage opens the shell
   with software rendering.
3. Inside it, `anypc-session-inner` starts `anypc-shelld` and opens the shell
   UI in a full-screen browser.
4. Games launched from the shell open on top of it; quitting a game returns to
   the shell. The player remains in the console session.

## Updating a running system

```sh
sudo bootc switch anypc.cubx-romania.ro/anypc-os:stable   # first time
sudo bootc upgrade                          # later
sudo bootc rollback                         # go back one version
```

## Store and system updates

The AnyPC catalog controls which applications the console offers. Packages are
downloaded from Flathub, with its signing key provided by the pinned repository
configuration. Steam opens its own storefront and handles Valve accounts and purchases.
The console account has no administrator group membership.

The x86-64 system update reference is anypc.cubx-romania.ro/anypc-os:stable.
To publish a tested release on the static update host, run

```sh
python3 build/publish-update.py out/AnyPC-OS-Installer-x86_64.iso /srv/anypc-preview
```

The publisher also accepts the same verified OCI layout used to build the ISO.
Serve /v2/ over HTTPS with GET and HEAD, the OCI manifest media type and the
Docker-Content-Digest header. Disable compression and content rewriting on
registry responses. Serve the stable tag with no-store caching. It verifies the config and every layer
before atomically replacing the stable tag. Older digest-addressed objects stay
available during concurrent downloads. The installed system can check, stage,
restart and roll back using its System settings. Publishing credentials remain
on the release host. The existing base ISO can also be remastered with
--system-oci and a verified bootable OCI layout.
