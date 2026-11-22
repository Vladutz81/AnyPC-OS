#!/usr/bin/env bash
# Build only the pinned native CPU diagnostics, with assertions enabled.
set -euo pipefail
manifest=${1:?manifest path required}
manifest=$(realpath "$manifest")
dest=${DESTDIR:?DESTDIR must name the staging root}
[[ "$dest" == /* && "$dest" != / ]] || { echo "Use an absolute staging root" >&2; exit 1; }
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
revision=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["revision"])' "$manifest")
sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive_sha256"])' "$manifest")
[[ "$revision" =~ ^[0-9a-f]{40}$ && "$sha" =~ ^[0-9a-f]{64}$ ]]
curl --proto '=https' --fail --location --retry 3 --silent --show-error \
    "https://codeload.github.com/ItsNotRexed/Leonida/tar.gz/$revision" -o "$work/source.tar.gz"
printf '%s  %s\n' "$sha" "$work/source.tar.gz" | sha256sum -c -
tar -xzf "$work/source.tar.gz" --no-same-owner -C "$work"
source_dir="$work/Leonida-$revision"
mapfile -t targets < <(python3 -c 'import json,sys; print("\n".join(json.load(open(sys.argv[1]))["checks"]))' "$manifest")
cmake -S "$source_dir/runtime" -B "$work/build" -G Ninja -DBUILD_TESTING=ON \
    -DCMAKE_BUILD_TYPE=Debug '-DCMAKE_CXX_FLAGS_DEBUG=-O2 -g0'
cmake --build "$work/build" --parallel 2 --target "${targets[@]}"
(cd "$work/build" && ctest --output-on-failure)
install -d "$dest/usr/libexec/anypc/leonida" "$dest/usr/share/licenses/leonida" \
    "$dest/usr/share/anypc/sources"
for target in "${targets[@]}"; do
    [[ "$target" =~ ^[a-z0-9_]+$ ]]
    install -m 0755 "$work/build/$target" "$dest/usr/libexec/anypc/leonida/$target"
done
install -m 0644 "$manifest" "$dest/usr/libexec/anypc/leonida/manifest.json"
install -m 0644 "$source_dir/LICENSE" "$dest/usr/share/licenses/leonida/LICENSE"
printf '%s\n' "Leonida $revision · GPL-3.0-or-later" \
    "https://github.com/ItsNotRexed/Leonida/tree/$revision" \
    'Native CPU diagnostics only. No game loader or third-party rpf9 component is bundled.' \
    > "$dest/usr/share/licenses/leonida/SOURCE"
# Ship the selected diagnostics' corresponding source and its upstream CMake file.
# Do not include unrelated game data tools or the Windows loader's dependencies.
tar -czf "$dest/usr/share/anypc/sources/leonida-native-$revision.tar.gz" \
    -C "$source_dir" LICENSE runtime
