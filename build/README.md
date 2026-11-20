# Building the AnyPC OS image

AnyPC OS is built as a **bootable container** on top of Fedora's `bootc` base
image: the whole OS is one container image, updated atomically, with rollback.

> Status: the Containerfile has not been built in CI yet. Expect to fix package
> names or paths on the first real build.

## 1. Build the OS image

Needs Podman on a Linux machine.

```sh
podman build -f build/Containerfile -t localhost/anypc-os:dev .
```

## 2. Make an installer ISO or a disk image

Uses [bootc-image-builder](https://github.com/osbuild/bootc-image-builder).
`build/config.toml` creates the `player` account that the console session logs
into automatically. Change the password before building.

```sh
mkdir -p out
sudo podman run --rm -it --privileged --pull=newer \
  --security-opt label=type:unconfined_t \
  -v ./build/config.toml:/config.toml:ro \
  -v ./out:/output \
  -v /var/lib/containers/storage:/var/lib/containers/storage \
  quay.io/centos-bootc/bootc-image-builder:latest \
  --type anaconda-iso --local localhost/anypc-os:dev
```

Use `--type qcow2` instead to get a virtual-machine disk for testing.

## 3. Try it in a virtual machine

```sh
qemu-system-x86_64 -enable-kvm -m 4096 -smp 4 -cpu host \
  -device virtio-vga-gl -display gtk,gl=on \
  -drive file=out/qcow2/disk.qcow2,if=virtio
```

## What happens at boot

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
