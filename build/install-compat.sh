#!/usr/bin/env bash
# Install the upstream interoperability tools and the signed Flatpak source.
set -euo pipefail
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cd "$work"
base=https://github.com/boykopovar/AnyPS5/releases/download/v0.1.5
fetch() {
    curl --proto '=https' --fail --location --retry 3 --silent --show-error "$1" -o "$2"
    printf '%s  %s\n' "$3" "$2" | sha256sum -c -
}
fetch "$base/relinker-v0.1.5" relinker 6501ce4f4f28b26ebeebd34b79b84dbcd10a0ffdf331d21a766006d49e2e2bd1
fetch "$base/prx-linux-v0.1.5.tar.gz" libs.tar.gz b2769731214e0315d70ad682cd1ded1433d754f9e5286290dfdc768b43caff37
fetch https://raw.githubusercontent.com/boykopovar/AnyPS5/v0.1.5/LICENSE LICENSE de124e5a899ae4074ebf5c0f790494178ab66d310606b86203d67a6f3ef45168
dest=/usr/libexec/anypc/anyps5
install -d "$dest" /usr/share/licenses/anyps5 /usr/share/anypc
install -m 0755 relinker "$dest/relinker"
tar -xzf libs.tar.gz --no-same-owner -C "$dest"
install -m 0644 LICENSE /usr/share/licenses/anyps5/LICENSE
printf '%s\n' 'AnyPS5 v0.1.5, GPL-2.0-only' 'https://github.com/boykopovar/AnyPS5/tree/v0.1.5' > /usr/share/licenses/anyps5/SOURCE
fetch https://dl.flathub.org/repo/flathub.flatpakrepo apps.flatpakrepo 3371dd250e61d9e1633630073fefda153cd4426f72f4afa0c3373ae2e8fea03a
install -m 0644 apps.flatpakrepo /usr/share/anypc/apps.flatpakrepo
