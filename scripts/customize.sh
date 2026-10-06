#!/usr/bin/env bash
set -euo pipefail

# This script runs inside the cloned PonWrt source tree, after feeds install.
# Keep NAND/UBI layout untouched; only add runtime packages here.

# collect.py reads this file unconditionally, so it must always exist.
: > ./custom-package-commits.tsv

record_commit() {
  printf '%s\t%s\n' "$1" "$(git -C "$2" rev-parse HEAD)" >> ./custom-package-commits.tsv
}

remove_matches() {
  local pattern="$1"
  find ./package ./feeds/luci ./feeds/packages \
    -maxdepth 4 -type d -iname "*${pattern}*" 2>/dev/null \
    -print -exec rm -rf {} + || true
}

clone_direct() {
  local target="$1"
  local repo="$2"
  local branch="$3"

  remove_matches "$target"
  git clone --depth=1 --single-branch --branch "$branch" \
    "https://github.com/${repo}.git" "./package/${target}"
  record_commit "$repo" "./package/${target}"
}

# The XG-040G-TF image is now built entirely from the PonWrt feeds; no external
# package source is imported.
#
# The Airoha NPU management page used to be imported here from
# bingoguo93/luci-app-airoha-npu, but that repository now returns 404 and the
# package is not part of any PonWrt feed, so importing it can only fail. The NPU
# firmware (airoha-en7581-npu-firmware) and hardware offload stay in the image
# and can be inspected from the shell. To bring the page back, clone it into
# ./package/ and add CONFIG_PACKAGE_luci-app-airoha-npu=y to
# config/common.config plus the same entry in config/required-packages.txt.
# The helpers above are the supported way to do that.

# This unselected audio package has a circular codec dependency with this
# source/feed snapshot. Exclude only its installed feed symlink so the
# Kconfig parser can load a clean menu; no requested firmware package uses it.
if [ -L ./package/feeds/packages/squeezelite ]; then
  rm ./package/feeds/packages/squeezelite
fi

# Force package metadata to be regenerated after adding/removing package trees.
rm -rf ./tmp

echo "Third-party package import completed."