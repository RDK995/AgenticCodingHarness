#!/usr/bin/env bash
set -euo pipefail
"$(CDPATH= cd -- "$(dirname -- "$0")/../_support" && pwd)/run-scenario.sh" accuracy-regression
