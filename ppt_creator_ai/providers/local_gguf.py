from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    review_presentation_density,
    suggest_image_queries_from_briefing,
    summarize_text_to_executive_bullets,
)
from ppt_creator_ai.providers.base import BriefingGenerationResult


class PPTAgentLocalProvider:
    name = "pptagent_local"
    description = "Runs a local GGUF model such as PPTAgent via llama.cpp / llama-cli."

    def playground_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def models_dir(self) -> Path:
        return self.playground_root() / "models"

    def resolve_model_path(self, model_input: str | None = None) -> Path:
        requested = (model_input or os.environ.get("PPT_CREATOR_AI_GGUF_MODEL") or "PPTAgent").strip()
        candidate = Path(requested)
        if candidate.is_file():
            return candidate.resolve()

        models = sorted(self.models_dir().rglob("*.gguf"))
        if not models:
            raise FileNotFoundError("No local .gguf models were found under models/")

        requested_lower = requested.lower()
        exact = [path for path in models if path.name.lower() == requested_lower]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise ValueError(f"More than one exact GGUF match found for: {requested}")

        partial = [path for path in models if requested_lower in path.name.lower()]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            options = ", ".join(path.name for path in partial)
            raise ValueError(f"More than one GGUF partial match found for '{requested}': {options}")

        raise FileNotFoundError(f"No GGUF model matched: {requested}")

    def build_prompt(self, briefing: BriefingInput, *, theme_name: str | None = None) -> str:
        effective_theme = theme_name or briefing.theme
        briefing_payload = briefing.model_dump(mode="json")
        return (
            "You are generating structured JSON for a PowerPoint deck renderer. "
            "Return only valid JSON with top-level keys 'presentation' and 'slides'. "
            "Do not wrap the result in markdown. Do not explain your reasoning. "
            "Use only these slide types: title, section, agenda, bullets, cards, metrics, chart, image_text, timeline, comparison, two_column, table, faq, summary, closing. "
            "Prefer concise executive slides and avoid overly dense content. "
            f"Use theme '{effective_theme}'.\n\n"
            "Structured briefing JSON:\n"
            f"{json.dumps(briefing_payload, ensure_ascii=False, indent=2)}\n\n"
            "Return a single JSON object now."
        )

    def run_model(self, model_path: Path, prompt: str) -> str:
        if shutil.which("llama-cli") is None:
            raise RuntimeError("llama-cli was not found in PATH. Install llama.cpp first.")

        ctx_size = os.environ.get("PPT_CREATOR_AI_CTX_SIZE", "8192")
        max_tokens = os.environ.get("PPT_CREATOR_AI_MAX_TOKENS", "1800")
        gpu_layers = os.environ.get("PPT_CREATOR_AI_GPU_LAYERS", "-1")
        temperature = os.environ.get("PPT_CREATOR_AI_TEMPERATURE", "0.2")
        timeout_seconds = int(os.environ.get("PPT_CREATOR_AI_TIMEOUT_SECONDS", "180"))
        raw_output_path = os.environ.get("PPT_CREATOR_AI_RAW_OUTPUT_PATH")

        command = [
            "llama-cli",
            "-m",
            str(model_path),
            "-c",
            ctx_size,
            "-ngl",
            gpu_layers,
            "-n",
            max_tokens,
            "--temp",
            temperature,
            "--no-conversation",
            "--simple-io",
            "-p",
            prompt,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                stdin=subprocess.DEVNULL,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            partial_output = ((exc.stdout or "") + (f"\n{exc.stderr}" if exc.stderr else "")).strip()
            if raw_output_path:
                Path(raw_output_path).write_text(partial_output + "\n", encoding="utf-8")
            raise RuntimeError(
                "llama-cli timed out before finishing. This often means the model is too slow or entered an unexpected mode. "
                f"Increase PPT_CREATOR_AI_TIMEOUT_SECONDS if needed. Partial output: {partial_output[:400]}"
            ) from exc
        output = (completed.stdout or "") + (f"\n{completed.stderr}" if completed.stderr else "")
        if raw_output_path:
            Path(raw_output_path).write_text(output + "\n", encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(f"llama-cli failed with exit code {completed.returncode}: {output.strip()}")
        return output

    def extract_json_payload(self, text: str) -> dict[str, object]:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and "presentation" in candidate and "slides" in candidate:
                return candidate
        raise ValueError("Could not extract presentation JSON from model output")

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
    ) -> BriefingGenerationResult:
        model_path = self.resolve_model_path()
        prompt = self.build_prompt(briefing, theme_name=theme_name)
        raw_output = self.run_model(model_path, prompt)
        payload = self.extract_json_payload(raw_output)
        spec = PresentationInput.model_validate(payload)
        normalized_payload = spec.model_dump(mode="json")

        summary_source = " ".join(
            filter(
                None,
                [briefing.objective, briefing.context, *briefing.key_messages[:3], *briefing.recommendations[:3]],
            )
        )
        analysis = {
            "briefing_title": briefing.title,
            "provider": self.name,
            "model_path": str(model_path),
            "theme": spec.presentation.theme,
            "generated_slide_count": len(spec.slides),
            "executive_summary_bullets": briefing.recommendations[:3]
            or summarize_text_to_executive_bullets(summary_source, max_bullets=3),
            "image_suggestions": suggest_image_queries_from_briefing(briefing),
            "density_review": review_presentation_density(spec),
        }
        return BriefingGenerationResult(
            provider_name=self.name,
            payload=normalized_payload,
            analysis=analysis,
        )
