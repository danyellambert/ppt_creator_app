#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"
"$ROOT/.conda-env/bin/hf" cache prune --cache-dir "$HF_HUB_CACHE" "$@"
