#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import time


def pick_device() -> tuple[str, object | None]:
    import torch

    if torch.backends.mps.is_available():
      return "mps", torch.float16
    return "cpu", None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a causal LM from Hugging Face with Transformers.")
    parser.add_argument("--model", required=True, help="HF repo id or local model directory")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--load-in-8bit", action="store_true")
    args = parser.parse_args()

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except Exception as exc:
        print(f"[ERROR] Failed to import required packages: {exc}", file=sys.stderr)
        return 1

    device, torch_dtype = pick_device()
    print(f"[INFO] device={device}")
    print(f"[INFO] model={args.model}")
    hf_home = os.environ.get("HF_HOME")
    if hf_home:
        print(f"[INFO] HF_HOME={hf_home}")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=args.trust_remote_code,
    )

    model_kwargs: dict = {
        "trust_remote_code": args.trust_remote_code,
    }

    if device == "mps":
        model_kwargs["torch_dtype"] = torch_dtype

    if args.load_in_8bit:
        model_kwargs["load_in_8bit"] = True

    start_load = time.time()
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)
    print(f"[INFO] load_seconds={time.time() - start_load:.2f}")

    if device != "cpu":
        model = model.to(device)

    inputs = tokenizer(args.prompt, return_tensors="pt")
    if device != "cpu":
        inputs = {k: v.to(device) for k, v in inputs.items()}

    start_gen = time.time()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )
    print(f"[INFO] gen_seconds={time.time() - start_gen:.2f}")

    text = tokenizer.decode(output[0], skip_special_tokens=True)
    print("\n===== OUTPUT =====\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
