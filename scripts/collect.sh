#!/usr/bin/env bash
set -euo pipefail
# Usage from CI repository root: bash scripts/collect.sh [source-dir] [output-dir]
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$(realpath "${1:-openwrt}")"
mkdir -p "${2:-output}"
OUTPUT_DIR="$(realpath "${2:-output}")"
TARGET_DIR="$SOURCE_DIR/bin/targets/airoha/an7581"
BOARD=nokia_xg-040g-md-ubi

one_file() {
  local pattern="$1"
  local -a matches
  mapfile -t matches < <(find "$TARGET_DIR" -maxdepth 1 -type f -name "$pattern" | sort)
  if [ "${#matches[@]}" -ne 1 ]; then
    echo "ERROR: expected exactly one $pattern; found ${#matches[@]}" >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}
SYSUPGRADE="$(one_file "*${BOARD}-squashfs-sysupgrade.itb")"
RECOVERY="$(one_file "*${BOARD}-initramfs-recovery.itb")"
MANIFEST="$(one_file "*${BOARD}.manifest")"
FWTOOL="$SOURCE_DIR/staging_dir/host/bin/fwtool"
test -x "$FWTOOL"
"$FWTOOL" -q -i "$OUTPUT_DIR/sysupgrade-metadata.json" "$SYSUPGRADE"
python3 "$CI_DIR/scripts/validate.py" config "$SOURCE_DIR/.config"
python3 "$CI_DIR/scripts/validate.py" images \
  "$OUTPUT_DIR/sysupgrade-metadata.json" "$TARGET_DIR/profiles.json" "$MANIFEST"

cp "$SYSUPGRADE" "$RECOVERY" "$MANIFEST" "$OUTPUT_DIR/"
cp "$TARGET_DIR/profiles.json" "$OUTPUT_DIR/profiles.json"
cp "$SOURCE_DIR/.config" "$OUTPUT_DIR/build.config"
cp "$SOURCE_DIR/feeds.conf.default" "$OUTPUT_DIR/feeds.conf.default"
if [ -s "$SOURCE_DIR/requested-packages-dropped.txt" ]; then
  cp "$SOURCE_DIR/requested-packages-dropped.txt" "$OUTPUT_DIR/"
fi

# Record the exact source, feeds and imported package repositories used.
{
  printf 'component\tcommit\n'
  printf 'ponwrt\t%s\n' "$(git -C "$SOURCE_DIR" rev-parse HEAD)"
  while IFS= read -r -d '' gitdir; do
    repo="$(dirname "$gitdir")"
    printf '%s\t%s\n' "${repo#"$SOURCE_DIR/"}" "$(git -C "$repo" rev-parse HEAD)"
  done < <(find "$SOURCE_DIR/feeds" "$SOURCE_DIR/package" -maxdepth 3 -name .git -type d -print0)
} > "$OUTPUT_DIR/source-commits.tsv"
if [ -f "$SOURCE_DIR/custom-package-commits.tsv" ]; then
  cat "$SOURCE_DIR/custom-package-commits.tsv" >> "$OUTPUT_DIR/source-commits.tsv"
fi
(cd "$OUTPUT_DIR" && sha256sum *.itb > SHA256SUMS)
