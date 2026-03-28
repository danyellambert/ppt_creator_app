from __future__ import annotations

from ppt_creator_ai.briefing import (
    BriefingInput,
    build_briefing_analysis,
    generate_presentation_payload_from_briefing,
)
from ppt_creator_ai.providers.base import BriefingGenerationResult


class HeuristicBriefingProvider:
    name = "heuristic"
    description = "Rule-based provider that generates deck JSON and analysis without external LLM calls."

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        payload = generate_presentation_payload_from_briefing(
            briefing,
            theme_name=theme_name,
            feedback_messages=feedback_messages,
        )
        analysis = build_briefing_analysis(
            briefing,
            theme_name=theme_name,
            feedback_messages=feedback_messages,
        )
        return BriefingGenerationResult(
            provider_name=self.name,
            payload=payload,
            analysis=analysis,
        )
