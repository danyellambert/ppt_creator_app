#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "This will remove the entire folder: $ROOT"
read -r -p "Type YES to continue: " ANSWER
if [ "$ANSWER" != "YES" ]; then
  echo "Aborted."
  exit 0
fi

if command -v conda >/dev/null 2>&1 && [ -d "$ROOT/.conda-env" ]; then
  conda env remove -p "$ROOT/.conda-env" -y || true
fi

rm -rf "$ROOT"
