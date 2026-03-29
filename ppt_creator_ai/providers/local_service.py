from __future__ import annotations

import json
import os
from urllib import error, request

from ppt_creator_ai.briefing import BriefingInput
from ppt_creator_ai.providers.base import BriefingGenerationResult, DeckCritiqueResult


class LocalServiceBriefingProvider:
    name = "local_service"
    description = "Delegates briefing-to-deck generation to the external persisted hf_local_llm_service over HTTP."

    def resolve_base_url(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_SERVICE_URL") or "http://127.0.0.1:8788").strip().rstrip("/")

    def resolve_provider_name(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_SERVICE_PROVIDER") or "ollama").strip().lower()

    def resolve_model_name(self) -> str:
        return (os.environ.get("PPT_CREATOR_AI_SERVICE_MODEL") or "llama3.1").strip()

    def resolve_timeout_seconds(self) -> int:
        return int(os.environ.get("PPT_CREATOR_AI_SERVICE_TIMEOUT_SECONDS", "180"))

    def _request_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        base_url = self.resolve_base_url()
        req = request.Request(
            f"{base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.resolve_timeout_seconds()) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.URLError as exc:
            raise RuntimeError(
                f"Could not reach hf_local_llm_service at {base_url}. Start the local persisted service first. Details: {exc.reason}"
            ) from exc

        try:
            response_payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"hf_local_llm_service returned invalid JSON: {exc.msg}") from exc

        if not isinstance(response_payload, dict):
            raise RuntimeError("hf_local_llm_service returned a non-object JSON response")
        if response_payload.get("error"):
            raise RuntimeError(str(response_payload["error"]))
        return response_payload

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        payload = self._request_json(
            "/v1/presentation/generate",
            {
                "provider_name": self.resolve_provider_name(),
                "model_name": self.resolve_model_name(),
                "briefing": briefing.model_dump(mode="json"),
                "theme_name": theme_name,
                "feedback_messages": feedback_messages or [],
            },
        )
        return BriefingGenerationResult(
            provider_name=str(payload.get("provider_name") or self.name),
            payload=dict(payload.get("payload") or {}),
            analysis=dict(payload.get("analysis") or {}),
        )

    def revise_generated_deck(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        payload = self._request_json(
            "/v1/presentation/revise",
            {
                "provider_name": self.resolve_provider_name(),
                "model_name": self.resolve_model_name(),
                "briefing": briefing.model_dump(mode="json"),
                "current_payload": current_payload,
                "review": review,
                "slide_critiques": slide_critiques,
                "theme_name": theme_name,
                "feedback_messages": feedback_messages or [],
            },
        )
        return BriefingGenerationResult(
            provider_name=str(payload.get("provider_name") or self.name),
            payload=dict(payload.get("payload") or {}),
            analysis=dict(payload.get("analysis") or {}),
        )

    def critique_generated_deck(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> DeckCritiqueResult:
        payload = self._request_json(
            "/v1/presentation/critique",
            {
                "provider_name": self.resolve_provider_name(),
                "model_name": self.resolve_model_name(),
                "briefing": briefing.model_dump(mode="json"),
                "current_payload": current_payload,
                "review": review,
                "slide_critiques": slide_critiques,
                "theme_name": theme_name,
                "feedback_messages": feedback_messages or [],
            },
        )
        return DeckCritiqueResult(
            provider_name=str(payload.get("provider_name") or self.name),
            critiques=[item for item in (payload.get("critiques") or []) if isinstance(item, dict)],
            analysis=dict(payload.get("analysis") or {}),
        )