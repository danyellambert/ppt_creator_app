#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <repo_or_revision> [more_ids...]"
  echo "Example: $0 model/Qwen/Qwen2.5-3B-Instruct"
  exit 1
fi

"$ROOT/.conda-env/bin/hf" cache rm --cache-dir "$HF_HUB_CACHE" "$@"
