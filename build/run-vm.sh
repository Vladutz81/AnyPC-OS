#!/usr/bin/env bash
# Boot a preinstalled AnyPC qcow2 with persistent, per-disk UEFI state.
set -euo pipefail

usage() {
    cat <<'HELP'
Usage: build/run-vm.sh DISK.qcow2 [-- QEMU_ARGUMENTS...]
       build/run-vm.sh --help

Boot a preinstalled AnyPC disk in a window. Install qemu-system-x86_64,
qemu-img and OVMF first. UEFI state is saved beside the disk as
DISK.qcow2.uefi-vars.fd and reused on later boots.

KVM is used when /dev/kvm is accessible. Otherwise QEMU uses slower CPU
emulation. The VM has 4 GiB RAM, 4 CPUs, virtio graphics, network, keyboard
and a USB tablet. Arguments after -- are passed directly to QEMU.

Examples:
  build/run-vm.sh out/qcow2/disk.qcow2
  build/run-vm.sh disk.qcow2 -- -display none -serial stdio

For a custom firmware installation, set both ANYPC_OVMF_CODE and
ANYPC_OVMF_VARS to matching OVMF code and variable-template files.
HELP
}

fail() { printf 'AnyPC VM: %s\n' "$*" >&2; exit 1; }

if [[ ${1:-} == --help || ${1:-} == -h ]]; then
    usage
    exit 0
fi
if (( $# == 0 )); then
    usage >&2
    exit 2
fi
disk_argument=$1
shift
if (( $# > 0 )); then
    [[ $1 == -- ]] || fail 'Put additional QEMU arguments after --.'
    shift
fi
for tool in qemu-system-x86_64 qemu-img realpath; do
    command -v "$tool" >/dev/null || fail "Install $tool before starting the VM."
done
[[ -f $disk_argument && -r $disk_argument && -w $disk_argument ]] || fail 'Choose a readable, writable qcow2 disk file.'
disk=$(realpath -- "$disk_argument")
qemu-img info -f qcow2 --output=json "$disk" >/dev/null || fail 'The disk could not be opened as qcow2.'

code=${ANYPC_OVMF_CODE:-}
template=${ANYPC_OVMF_VARS:-}
if [[ -n $code || -n $template ]]; then
    [[ -n $code && -n $template ]] || fail 'Set both ANYPC_OVMF_CODE and ANYPC_OVMF_VARS.'
else
    for pair in \
        /usr/share/OVMF/OVMF_CODE_4M.fd:/usr/share/OVMF/OVMF_VARS_4M.fd \
        /usr/share/OVMF/OVMF_CODE.fd:/usr/share/OVMF/OVMF_VARS.fd \
        /usr/share/edk2/ovmf/OVMF_CODE.fd:/usr/share/edk2/ovmf/OVMF_VARS.fd \
        /usr/share/edk2/x64/OVMF_CODE.4m.fd:/usr/share/edk2/x64/OVMF_VARS.4m.fd; do
        if [[ -r ${pair%%:*} && -r ${pair#*:} ]]; then
            code=${pair%%:*}
            template=${pair#*:}
            break
        fi
    done
fi
[[ -f $code && -r $code && -f $template && -r $template ]] || fail 'Install OVMF or set the matching ANYPC_OVMF_CODE and ANYPC_OVMF_VARS paths.'
code=$(realpath -- "$code")
vars="$disk.uefi-vars.fd"
[[ ! -L $vars ]] || fail 'The UEFI state file must not be a symbolic link.'
if [[ ! -e $vars ]]; then
    temporary=$(mktemp "$vars.tmp.XXXXXX") || fail 'Cannot create UEFI state beside the disk.'
    trap 'rm -f -- "$temporary"' EXIT
    cp -- "$template" "$temporary"
    chmod 0600 "$temporary"
    # A hard link publishes the complete copy without replacing existing state.
    if ! ln -- "$temporary" "$vars" 2>/dev/null; then
        [[ -f $vars && ! -L $vars ]] || fail 'Cannot save UEFI state beside the disk.'
    fi
    rm -- "$temporary"
    trap - EXIT
fi
[[ -f $vars && -r $vars && -w $vars ]] || fail 'The UEFI state file must be readable and writable.'
[[ $(wc -c < "$vars") -eq $(wc -c < "$template") ]] || fail 'The saved UEFI state size differs from this firmware template. Use its matching OVMF pair.'

acceleration=tcg
cpu=max
if [[ -r /dev/kvm && -w /dev/kvm ]]; then
    acceleration=kvm
    cpu=host
else
    printf 'AnyPC VM: KVM unavailable, using slower CPU emulation.\n' >&2
fi
# QEMU key-value options escape a literal comma by doubling it.
disk_option=${disk//,/,,}
code_option=${code//,/,,}
vars_option=${vars//,/,,}
exec qemu-system-x86_64 \
    -name 'AnyPC OS' -machine "q35,accel=$acceleration" -cpu "$cpu" \
    -m 4096 -smp 4 \
    -drive "if=pflash,format=raw,readonly=on,file=$code_option" \
    -drive "if=pflash,format=raw,file=$vars_option" \
    -drive "if=virtio,format=qcow2,file=$disk_option" \
    -vga virtio -device qemu-xhci -device usb-tablet \
    -nic user,model=virtio-net-pci -boot order=c "$@"
