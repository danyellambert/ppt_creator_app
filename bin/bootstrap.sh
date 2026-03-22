#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

mkdir -p "$ROOT/.hf" "$ROOT/outputs" "$ROOT/models" "$ROOT/tmp"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda was not found in PATH."
  echo "Open a terminal where conda works, then run this script again."
  exit 1
fi

if [ ! -d "$ROOT/.conda-env" ]; then
  echo "[INFO] Creating local conda env at $ROOT/.conda-env"
  conda create -y -p "$ROOT/.conda-env" python="$PYTHON_VERSION"
else
  echo "[INFO] Reusing existing env at $ROOT/.conda-env"
fi

PIP="$ROOT/.conda-env/bin/pip"

"$PIP" install --upgrade pip setuptools wheel
"$PIP" install -U "huggingface_hub[cli]" transformers accelerate safetensors sentencepiece protobuf
"$PIP" install -U torch

if [[ "$(uname -s)" == "Darwin" ]] && [[ "$(uname -m)" == "arm64" ]]; then
  "$PIP" install -U mlx mlx-lm
  echo "[INFO] Installed MLX + MLX-LM for Apple Silicon."
else
  echo "[INFO] Skipping MLX install because this machine is not macOS arm64."
fi

cat > "$ROOT/bin/env.sh" <<'ENVEOF'
#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export HF_HOME="$ROOT/.hf"
export HF_HUB_CACHE="$HF_HOME/hub"
export HF_XET_CACHE="$HF_HOME/xet"
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export HF_ASSETS_CACHE="$HF_HOME/assets"
export PYTORCH_ENABLE_MPS_FALLBACK=1
mkdir -p "$HF_HOME" "$HF_HUB_CACHE" "$HF_XET_CACHE" "$HF_ASSETS_CACHE" "$ROOT/outputs" "$ROOT/models" "$ROOT/tmp"
ENVEOF
chmod +x "$ROOT/bin/env.sh"

cat > "$ROOT/bin/activate.sh" <<'ACTEOF'
#!/usr/bin/env bash
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/bin/env.sh"
source "$ROOT/.conda-env/bin/activate"
echo "hf_llm_playground ready"
echo "ROOT=$ROOT"
echo "HF_HOME=$HF_HOME"
ACTEOF
chmod +x "$ROOT/bin/activate.sh"

echo "[INFO] Bootstrap finished."
echo "Next:"
echo "  cd \"$ROOT\""
echo "  source bin/activate.sh"
echo "  ./.conda-env/bin/hf auth login   # only if needed"
