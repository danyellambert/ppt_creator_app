# HF LLM Playground

This is a deleteable local sandbox for testing Hugging Face text models without polluting your main machine setup.

It follows the same idea as your `sd35_mlx_sandbox`, but for LLMs:

- local Conda environment inside the folder
- local Hugging Face cache inside the folder
- easy download / test / remove workflow
- optional bridge back into Ollama for GGUF models you decide to keep

---

## Recommended folder structure

```text
hf_llm_playground/
├── .conda-env/
├── .hf/
├── bin/
├── models/
├── outputs/
├── scripts/
├── tmp/
└── README_hf_llm_playground.md
```

What each part does:

- `.conda-env/` -> isolated Python environment
- `.hf/` -> local Hugging Face cache and token storage for this sandbox
- `bin/` -> helper shell scripts
- `models/` -> optional local copies / downloads / conversions
- `outputs/` -> saved outputs if you want to keep logs or generations
- `scripts/` -> Python helpers
- `tmp/` -> temporary work area

---

## What this playground is for

Use it when you want to try repos from Hugging Face quickly and then delete everything later.

Best fit:

1. **Transformers / Safetensors repos**
   - try them with `run_transformers.sh`

2. **MLX-compatible repos on Apple Silicon**
   - try them with `run_mlx.sh`

3. **GGUF repos that you may later keep in Ollama**
   - download them here first if you want
   - if you like them, import into Ollama with `import_gguf_to_ollama.sh`

---

## Important limitation

There is no single runtime that truly runs every repo on the Hub.

Use this mental model:

- **GGUF** -> Ollama / LM Studio / llama.cpp
- **MLX repo** -> MLX-LM
- **regular HF Transformers repo** -> Transformers

That is exactly why this playground uses multiple lanes instead of forcing everything into Ollama.

---

## 1) First-time setup

Open Terminal and go into the folder:

```bash
cd ~/hf_llm_playground
```

```bash
cd ~/hf_llm_playground
CONDA_SOLVER=classic conda create -y -p "$PWD/.conda-env" python=3.11
```

```bash
cd ~/hf_llm_playground

"$PWD/.conda-env/bin/python" -V
"$PWD/.conda-env/bin/python" -m pip install --upgrade pip setuptools wheel

"$PWD/.conda-env/bin/python" -m pip install -U \
  "huggingface_hub[cli]" \
  transformers \
  accelerate \
  safetensors \
  sentencepiece \
  protobuf \
  torch \
  mlx \
  mlx-lm
```

```bash
cd ~/hf_llm_playground

"$PWD/.conda-env/bin/python" -c "import transformers, torch, huggingface_hub; print('ok transformers/torch/hf')"
"$PWD/.conda-env/bin/python" -c "import mlx, mlx_lm; print('ok mlx/mlx_lm')"
```

```bash
cd ~/hf_llm_playground
export HF_PLAYGROUND_ROOT="$PWD"
export HF_HOME="$PWD/.hf"
export HF_HUB_CACHE="$PWD/.hf/hub"
export TRANSFORMERS_CACHE="$PWD/.hf/transformers"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PATH="$PWD/.conda-env/bin:$PATH"
```

```bash
which python
python -V
```

```bash
python - <<'PY'
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_id = "Qwen/Qwen2.5-0.5B-Instruct"

tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype="auto",
    device_map="auto"
)

prompt = "Explique em uma frase o que é uma apresentação PowerPoint."
inputs = tok(prompt, return_tensors="pt").to(model.device)
out = model.generate(**inputs, max_new_tokens=60)
print(tok.decode(out[0], skip_special_tokens=True))
PY
```

```bash
python -m mlx_lm.generate \
  --model mlx-community/Qwen2.5-0.5B-Instruct-4bit \
  --prompt "Say in one sentence what PPTAgent is." \
  --max-tokens 40
```

etapa abaixo so na 1ra vez:

```bash
cd ~/hf_llm_playground

export HF_PLAYGROUND_ROOT="$PWD"
export HF_HOME="$PWD/.hf"
export HF_HUB_CACHE="$PWD/.hf/hub"
export TRANSFORMERS_CACHE="$PWD/.hf/transformers"
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PATH="$PWD/.conda-env/bin:$PATH"

hf auth login
```

Coloca o token

coloca n

A partir daqui começa p cada modelo novo

```bash
cd ~/hf_llm_playground

export HF_HOME="$PWD/.hf"
export HF_HUB_CACHE="$PWD/.hf/hub"
export TRANSFORMERS_CACHE="$PWD/.hf/transformers"
export PATH="$PWD/.conda-env/bin:$PATH"

hf auth whoami
```

Aqui começa pro modelo especifico mradermacher/PPTAgent-coder-3B-GGUF

Aqui é pra fazer um dry run - mostrar quais arquivos seriam baixados e seus tamanhos, sem baixar nada ainda. E o --include serve para filtrar por padrão de nome.

```bash
hf download mradermacher/PPTAgent-coder-3B-GGUF --dry-run --include "*.gguf"
```

O que vem deppois tem o --local-dir que baixa para a pasta que você escolheu; sem isso, o download vai para o cache do Hugging Face definido por HF_HOME. O de baixo so pega 1 modelo dentro do repertorio  - *Q4_K_M*.gguf
```bash
mkdir -p "$PWD/models/pptagent"

hf download mradermacher/PPTAgent-coder-3B-GGUF \
  --include "*Q4_K_M*.gguf" \
  --local-dir "$PWD/models/pptagent"
```

Ou senao baixa direto pelo nome que aparece no dry run: 
```bash
hf download mradermacher/PPTAgent-coder-3B.Q4_K_M.gguf --local-dir "$PWD/models/pptagent"
```


Pelo nome exato

```bash
cd ~/hf_llm_playground
bash bin/run_gguf_llama_cpp.sh PPTAgent-coder-3B.Q4_K_M.gguf
```
Por um pedaco de nome
```bash
bash bin/run_gguf_llama_cpp.sh PPTAgent
```

Com prompt direto
```bash
bash bin/run_gguf_llama_cpp.sh PPTAgent "Create a 6-slide presentation about AI copilots for sales teams."
````

Forçando CPU
```bash
GPU_LAYERS=0 bash bin/run_gguf_llama_cpp.sh PPTAgent
```

Contexto maior
```bash
CTX_SIZE=8192 MAX_TOKENS=500 bash bin/run_gguf_llama_cpp.sh PPTAgent "Create a detailed 8-slide deck about industrial AI."
```




Run:

```bash
bash bin/bootstrap.sh
```

Then activate the sandbox:

```bash
source bin/activate.sh
```

If you need a Hugging Face login:

```bash
./.conda-env/bin/hf auth login
```

If asked whether to add to git credential, answer `n`.

---

## 2) Every time you come back later

```bash
cd ~/hf_llm_playground
source bin/activate.sh
```

That restores the local HF cache paths and activates the local environment.

---

## 3) Fast tests

### A. Try a standard Transformers repo

```bash
./bin/run_transformers.sh Qwen/Qwen2.5-3B-Instruct "Explain what a landing page is"
```

If a model requires custom code:

```bash
./bin/run_transformers.sh some/model "hello" --trust-remote-code
```

### B. Try an MLX repo on Apple Silicon

```bash
./bin/run_mlx.sh mlx-community/Llama-3.2-3B-Instruct-4bit "Explain quantization simply" -m 256
```

### C. Download a repo into the local sandbox only

```bash
./bin/hf_download.sh Qwen/Qwen2.5-3B-Instruct --local-dir ./models/Qwen2.5-3B-Instruct
```

Then run it from the local folder:

```bash
./bin/run_transformers.sh ./models/Qwen2.5-3B-Instruct "Summarize the project"
```

---

## 4) Testing your PPTAgent GGUF case

For a GGUF repo like `mradermacher/PPTAgent-coder-3B-GGUF`, the normal path is still a GGUF runtime.

Example flow:

1. download the `.gguf` file into `models/`
2. test it with your preferred GGUF runtime
3. if you want it in Ollama permanently, import it

Example import into Ollama:

```bash
./bin/import_gguf_to_ollama.sh ./models/PPTAgent-coder-3B.Q4_K_M.gguf pptagent-coder-3b:q4km
```

---

## 5) Inspect / free space

### List what is in the local HF cache

```bash
./bin/cache_ls.sh
```

### Remove a repo or revision from the local HF cache

```bash
./bin/cache_rm.sh model/Qwen/Qwen2.5-3B-Instruct
```

### Remove detached snapshots

```bash
./bin/cache_prune.sh
```

---

## 6) Full deletion later

If you want to remove everything:

```bash
./bin/nuke_playground.sh
```

That removes:

- the local Conda environment
- the local Hugging Face cache for this sandbox
- all local downloads in this folder
- all helper scripts

---

## Practical decision rule

Use this playground when a model is still in the **"maybe"** stage.

Use Ollama only when the model has graduated into the **"I actually want this in my real workflow"** stage.
