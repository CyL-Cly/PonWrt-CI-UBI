#!/usr/bin/env bash
set -euo pipefail
# Run from the PonWrt source root, after feeds install and customize.sh.
CI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cat "$CI_DIR/config/xg040g-md-ubi.config" \
    "$CI_DIR/config/general-packages.config" \
    "$CI_DIR/config/pon-packages.config" > .config
make defconfig
python3 "$CI_DIR/scripts/validate.py" config .config
mkdir -p files
cp -a "$CI_DIR/files/." files/

# Record renamed/unavailable optional baseline symbols for review.
python3 - "$CI_DIR" <<'PY'
import pathlib
import sys
ci = pathlib.Path(sys.argv[1])
actual = set(pathlib.Path('.config').read_text().splitlines())
requested = set()
for path in sorted((ci / 'config').glob('*.config')):
    requested.update(line for line in path.read_text().splitlines()
                     if line.startswith('CONFIG_PACKAGE_') and line.endswith('=y'))
dropped = sorted(requested - actual)
pathlib.Path('requested-packages-dropped.txt').write_text(''.join(x + '\n' for x in dropped))
if dropped:
    print('Optional requested symbols unavailable after make defconfig:')
    print('\n'.join(dropped))
PY
