#!/usr/bin/env bash
set -euo pipefail
CI_DIR="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$CI_DIR/scripts/collect.py" "$@"
