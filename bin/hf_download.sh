#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <repo_id> [hf download args...]"
  echo "Example: $0 mistralai/Mistral-7B-Instruct-v0.3 --local-dir ./models/mistral-v0.3"
  exit 1
fi

"$ROOT/.conda-env/bin/hf" download "$@"
