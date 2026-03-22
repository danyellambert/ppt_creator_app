#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT/models"

MODEL_INPUT="${1:-}"
PROMPT="${2:-}"

MAX_TOKENS="${MAX_TOKENS:-300}"
CTX_SIZE="${CTX_SIZE:-4096}"
GPU_LAYERS="${GPU_LAYERS:--1}"
THREADS="${THREADS:-}"
CONV_MODE="${CONV_MODE:-auto}"   # auto | on | off

lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

usage() {
  cat <<USAGE
Usage:
  bash bin/run_gguf_llama_cpp.sh /absolute/path/to/model.gguf
  bash bin/run_gguf_llama_cpp.sh model.gguf
  bash bin/run_gguf_llama_cpp.sh partial_model_name
  bash bin/run_gguf_llama_cpp.sh partial_model_name "Your prompt here"
USAGE
}

if [[ -z "$MODEL_INPUT" ]]; then
  usage
  exit 1
fi

if ! command -v llama-cli >/dev/null 2>&1; then
  echo "[ERROR] llama-cli não encontrado no PATH."
  echo "Instale com: brew install llama.cpp"
  exit 1
fi

resolve_model() {
  local input="$1"
  local input_lc
  local matches=""
  local count=0
  local f=""
  local name=""
  local name_lc=""

  input_lc="$(lower "$input")"

  # 1) caminho direto
  if [[ -f "$input" ]]; then
    printf '%s\n' "$input"
    return 0
  fi

  # 2) match exato
  while IFS= read -r f; do
    name="$(basename "$f")"
    name_lc="$(lower "$name")"
    if [[ "$name_lc" == "$input_lc" ]]; then
      matches="${matches}${f}"$'\n'
      count=$((count + 1))
    fi
  done < <(find "$MODELS_DIR" -type f -name "*.gguf")

  if [[ $count -eq 1 ]]; then
    printf '%s' "$matches" | head -n 1
    return 0
  elif [[ $count -gt 1 ]]; then
    echo "[ERROR] Mais de um match exato encontrado para: $input"
    printf '%s' "$matches" | sed 's/^/ - /'
    return 2
  fi

  # 3) match parcial
  matches=""
  count=0
  while IFS= read -r f; do
    name="$(basename "$f")"
    name_lc="$(lower "$name")"
    case "$name_lc" in
      *"$input_lc"*)
        matches="${matches}${f}"$'\n'
        count=$((count + 1))
        ;;
    esac
  done < <(find "$MODELS_DIR" -type f -name "*.gguf")

  if [[ $count -eq 1 ]]; then
    printf '%s' "$matches" | head -n 1
    return 0
  elif [[ $count -gt 1 ]]; then
    echo "[ERROR] Mais de um match parcial encontrado para: $input"
    printf '%s' "$matches" | sed 's/^/ - /'
    echo
    echo "Seja mais específico."
    return 2
  fi

  echo "[ERROR] Nenhum modelo .gguf encontrado para: $input"
  echo "[INFO] Procurei dentro de: $MODELS_DIR"
  return 1
}

MODEL_PATH="$(resolve_model "$MODEL_INPUT")" || exit $?

CMD=(
  llama-cli
  -m "$MODEL_PATH"
  -c "$CTX_SIZE"
)

if [[ -n "$THREADS" ]]; then
  CMD+=(-t "$THREADS")
fi

if [[ -n "$GPU_LAYERS" ]]; then
  CMD+=(-ngl "$GPU_LAYERS")
fi

case "$CONV_MODE" in
  on)
    CMD+=(-cnv)
    ;;
  off)
    if [[ -z "$PROMPT" ]]; then
      echo "[ERROR] CONV_MODE=off exige um prompt."
      exit 1
    fi
    CMD+=(-p "$PROMPT" -n "$MAX_TOKENS")
    ;;
  auto)
    if [[ -n "$PROMPT" ]]; then
      CMD+=(-p "$PROMPT" -n "$MAX_TOKENS")
    else
      CMD+=(-cnv)
    fi
    ;;
  *)
    echo "[ERROR] CONV_MODE deve ser: auto, on ou off"
    exit 1
    ;;
esac

echo "[INFO] ROOT       = $ROOT"
echo "[INFO] MODELS_DIR = $MODELS_DIR"
echo "[INFO] MODEL      = $MODEL_PATH"
echo "[INFO] CTX_SIZE   = $CTX_SIZE"
echo "[INFO] GPU_LAYERS = $GPU_LAYERS"
if [[ -n "$THREADS" ]]; then
  echo "[INFO] THREADS    = $THREADS"
fi
if [[ -n "$PROMPT" ]]; then
  echo "[INFO] MODE       = one-shot"
else
  echo "[INFO] MODE       = interactive"
fi
echo

printf '[INFO] Command: '
printf '%q ' "${CMD[@]}"
echo
echo

exec "${CMD[@]}"
