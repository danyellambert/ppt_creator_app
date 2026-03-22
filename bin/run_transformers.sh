#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <repo_id_or_local_dir> <prompt> [extra python args...]"
  echo "Example: $0 Qwen/Qwen2.5-3B-Instruct 'Write a haiku about Rio' --max-new-tokens 128"
  exit 1
fi

REPO_ID="$1"
PROMPT="$2"
shift 2

"$ROOT/.conda-env/bin/python" "$ROOT/scripts/run_transformers.py" \
  --model "$REPO_ID" \
  --prompt "$PROMPT" \
  "$@"
