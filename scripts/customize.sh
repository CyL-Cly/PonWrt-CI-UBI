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
  # GIT_TERMINAL_PROMPT=0 turns a missing or private repository into an
  # immediate error instead of a blocking credential prompt.
  if ! GIT_TERMINAL_PROMPT=0 git clone --depth=1 --single-branch --branch "$branch" \
      "https://github.com/${repo}.git" "./package/${target}"; then
    echo "ERROR: cannot clone ${repo} (branch ${branch})." >&2
    echo "The source may have been removed, renamed or made private." >&2
    echo "Then update scripts/customize.sh, config/common.config and" >&2
    echo "config/required-packages.txt together, or drop the package." >&2
    exit 1
  fi
  if [ ! -f "./package/${target}/Makefile" ]; then
    echo "ERROR: ${repo} was cloned but ./package/${target}/Makefile is missing." >&2
    exit 1
  fi
  record_commit "$repo" "./package/${target}"
}

echo "Importing the third-party packages used by the package set..."

# Management page for the Airoha NPU, showing NPU state and reserved memory,
# Frame Engine counters, the PPE flow offload table and CPU frequency.
#
# It was originally taken from bingoguo93/luci-app-airoha-npu, which now returns
# 404 and is no longer listed among that owner's public repositories. This fork
# is used instead: it is a plain LuCI package whose directory name yields the
# luci-app-airoha-npu package and whose Makefile already includes
# $(TOPDIR)/feeds/luci/luci.mk, so it can be imported without any include
# fixup. Its register accesses need CONFIG_BUSYBOX_CONFIG_DEVMEM, which
# config/common.config already enables.
clone_direct "luci-app-airoha-npu" "rchen14b/luci-app-airoha-npu" "main"

# This unselected audio package has a circular codec dependency with this
# source/feed snapshot. Exclude only its installed feed symlink so the
# Kconfig parser can load a clean menu; no requested firmware package uses it.
if [ -L ./package/feeds/packages/squeezelite ]; then
  rm ./package/feeds/packages/squeezelite
fi

# Force package metadata to be regenerated after adding/removing package trees.
rm -rf ./tmp

echo "Third-party package import completed."