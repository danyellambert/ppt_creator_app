from __future__ import annotations

import json
import os
from pathlib import Path
from urllib import error, request

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    generate_presentation_payload_from_briefing,
    review_presentation_density,
    suggest_image_queries_from_briefing,
    summarize_text_to_executive_bullets,
)
from ppt_creator_ai.providers.base import BriefingGenerationResult
from ppt_creator_ai.providers.local_gguf import PPTAgentLocalProvider


class OllamaBriefingProvider:
    name = "ollama"
    description = "Runs a local Ollama model over HTTP to generate presentation JSON without external SaaS APIs."

    def __init__(self) -> None:
        self._structured_helper = PPTAgentLocalProvider()

    def resolve_base_url(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_OLLAMA_BASE_URL") or "http://127.0.0.1:11434").strip().rstrip("/")

    def resolve_model_name(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_OLLAMA_MODEL") or "llama3.1").strip()

    def build_prompt(self, briefing: BriefingInput, *, theme_name: str | None = None) -> str:
        return self._structured_helper.build_prompt(briefing, theme_name=theme_name)

    def request_generation(self, prompt: str, *, model_name: str) -> str:
        base_url = self.resolve_base_url()
        timeout_seconds = int(os.environ.get("PPT_CREATOR_AI_OLLAMA_TIMEOUT_SECONDS", "180"))
        raw_output_path = os.environ.get("PPT_CREATOR_AI_OLLAMA_RAW_OUTPUT_PATH")
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": float(os.environ.get("PPT_CREATOR_AI_OLLAMA_TEMPERATURE", "0.2")),
                "num_ctx": int(os.environ.get("PPT_CREATOR_AI_OLLAMA_CTX_SIZE", "8192")),
            },
        }
        req = request.Request(
            f"{base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {base_url}. Make sure 'ollama serve' is running. Details: {exc.reason}"
            ) from exc

        if raw_output_path:
            raw_output_file = Path(raw_output_path)
            raw_output_file.parent.mkdir(parents=True, exist_ok=True)
            raw_output_file.write_text(body + "\n", encoding="utf-8")

        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Ollama returned invalid JSON envelope: {exc.msg}") from exc

        if response_payload.get("error"):
            raise RuntimeError(f"Ollama generation failed: {response_payload['error']}")

        completion = response_payload.get("response")
        if not isinstance(completion, str) or not completion.strip():
            raise RuntimeError("Ollama did not return a textual completion in the 'response' field")
        return completion

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
    ) -> BriefingGenerationResult:
        model_name = self.resolve_model_name()
        prompt = self.build_prompt(briefing, theme_name=theme_name)
        raw_output = self.request_generation(prompt, model_name=model_name)
        payload = self._structured_helper.extract_json_payload(raw_output)
        normalized_payload = self._structured_helper.normalize_generated_payload(
            payload,
            briefing,
            theme_name=theme_name,
        )

        try:
            spec = PresentationInput.model_validate(normalized_payload)
        except Exception:
            fallback_payload = generate_presentation_payload_from_briefing(briefing, theme_name=theme_name)
            spec = PresentationInput.model_validate(fallback_payload)
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
            "model_name": model_name,
            "base_url": self.resolve_base_url(),
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
