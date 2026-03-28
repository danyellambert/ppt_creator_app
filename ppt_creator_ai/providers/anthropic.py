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


def _coerce_anthropic_content(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(
            str(item.get("text") or "")
            for item in value
            if isinstance(item, dict) and item.get("type") == "text"
        ).strip()
    return ""


class AnthropicBriefingProvider:
    name = "anthropic"
    description = "Calls the Anthropic Messages API to generate presentation JSON."

    def __init__(self) -> None:
        self._structured_helper = PPTAgentLocalProvider()

    def resolve_base_url(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_ANTHROPIC_BASE_URL") or "https://api.anthropic.com").strip().rstrip("/")

    def resolve_model_name(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_ANTHROPIC_MODEL") or "claude-3-5-haiku-latest").strip()

    def resolve_api_key(self) -> str:
        api_key = (os.environ.get("PPT_CREATOR_AI_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            raise RuntimeError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY or PPT_CREATOR_AI_ANTHROPIC_API_KEY."
            )
        return api_key

    def build_prompt(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> str:
        prompt = self._structured_helper.build_prompt(briefing, theme_name=theme_name)
        if feedback_messages:
            prompt += "\n\nAdditional regeneration guidance:\n- " + "\n- ".join(feedback_messages)
        return prompt

    def request_generation(self, prompt: str, *, model_name: str) -> str:
        api_key = self.resolve_api_key()
        base_url = self.resolve_base_url()
        timeout_seconds = int(os.environ.get("PPT_CREATOR_AI_ANTHROPIC_TIMEOUT_SECONDS", "180"))
        raw_output_path = os.environ.get("PPT_CREATOR_AI_ANTHROPIC_RAW_OUTPUT_PATH")
        payload = {
            "model": model_name,
            "max_tokens": int(os.environ.get("PPT_CREATOR_AI_ANTHROPIC_MAX_TOKENS", "1800")),
            "temperature": float(os.environ.get("PPT_CREATOR_AI_ANTHROPIC_TEMPERATURE", "0.2")),
            "messages": [{"role": "user", "content": prompt}],
        }
        req = request.Request(
            f"{base_url}/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach Anthropic at {base_url}. Check network connectivity and credentials. Details: {exc.reason}"
            ) from exc

        if raw_output_path:
            raw_output_file = Path(raw_output_path)
            raw_output_file.parent.mkdir(parents=True, exist_ok=True)
            raw_output_file.write_text(body + "\n", encoding="utf-8")

        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Anthropic returned invalid JSON envelope: {exc.msg}") from exc

        if response_payload.get("error"):
            details = response_payload["error"]
            message = details.get("message") if isinstance(details, dict) else details
            raise RuntimeError(f"Anthropic generation failed: {message}")

        completion = _coerce_anthropic_content(response_payload.get("content"))
        if not completion:
            raise RuntimeError("Anthropic response did not include textual content")
        return completion

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        model_name = self.resolve_model_name()
        prompt = self.build_prompt(briefing, theme_name=theme_name, feedback_messages=feedback_messages)
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
            "feedback_messages": feedback_messages or [],
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
