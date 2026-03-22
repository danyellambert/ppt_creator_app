#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <repo_id> <prompt> [extra mlx_lm.generate args...]"
  echo "Example: $0 mlx-community/Llama-3.2-3B-Instruct-4bit 'Explain transformers simply' -m 256"
  exit 1
fi

REPO_ID="$1"
PROMPT="$2"
shift 2

"$ROOT/.conda-env/bin/mlx_lm.generate" --model "$REPO_ID" --prompt "$PROMPT" "$@"
