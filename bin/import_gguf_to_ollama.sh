#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <path/to/model.gguf> <ollama_model_name>"
  echo "Example: $0 ./models/PPTAgent-coder-3B.Q4_K_M.gguf pptagent-coder-3b:q4km"
  exit 1
fi

GGUF_PATH="$1"
MODEL_NAME="$2"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

cat > "$WORKDIR/Modelfile" <<MODELEOF
FROM $GGUF_PATH
MODELEOF

( cd "$WORKDIR" && ollama create "$MODEL_NAME" )
echo "Imported into Ollama as: $MODEL_NAME"
