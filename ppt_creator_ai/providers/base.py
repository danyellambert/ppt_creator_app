from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ppt_creator_ai.briefing import BriefingInput


@dataclass(frozen=True)
class BriefingGenerationResult:
    provider_name: str
    payload: dict[str, object]
    analysis: dict[str, object]


class BriefingProvider(Protocol):
    name: str
    description: str

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
    ) -> BriefingGenerationResult: ...
