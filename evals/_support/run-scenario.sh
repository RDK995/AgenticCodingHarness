#!/usr/bin/env bash
set -euo pipefail

support_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
python3 "$support_dir/scaffold.py" "$1"
