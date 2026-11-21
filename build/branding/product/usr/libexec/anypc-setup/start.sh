#!/usr/bin/env bash
# Start the local setup shell on the installer media's Wayland compositor.
set -euo pipefail

cmdline=" $(cat /proc/cmdline) "
case "$cmdline" in
    *" inst.rescue "*|*" inst.text "*|*" inst.cmdline "*|*" inst.anypc-native "*)
        exec /usr/bin/anaconda
        ;;
esac

umask 077
mkdir -p -m 0700 /run/anypc-setup
export XDG_RUNTIME_DIR=/run/user/0
export XDG_SESSION_TYPE=wayland
export XDG_CONFIG_DIRS="/usr/share/anaconda:${XDG_CONFIG_DIRS:-/etc/xdg}"
export XDG_DATA_DIRS="/usr/share/anaconda/window-manager:${XDG_DATA_DIRS:-/usr/share}"
export GDK_BACKEND=wayland
export WAYLAND_DISPLAY=anypc-setup
if [[ "$cmdline" == *" inst.lang=ro_RO.UTF-8 "* ]]; then
    export LANG=ro_RO.UTF-8
fi

/usr/libexec/anaconda/run-in-new-session \
    --user root --service anaconda --session-type wayland --session-class user --vt 6 \
    gnome-kiosk --wayland --wayland-display "$WAYLAND_DISPLAY" \
    > /run/anypc-setup/display.log 2>&1 &
display_pid=$!
trap 'kill "$display_pid" 2>/dev/null || true' EXIT

for _ in {1..300}; do
    if [[ -S "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" ]]; then
        python3 /usr/libexec/anypc-setup/wizard.py
        exit
    fi
    kill -0 "$display_pid" 2>/dev/null || break
    sleep 0.1
done
printf '%s\n' 'AnyPC Setup could not open the graphical session. Use the troubleshooting menu after restarting.' >&2
exit 1
