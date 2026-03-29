from __future__ import annotations

from ppt_creator_ai.providers.base import (
    BriefingGenerationResult,
    BriefingProvider,
    DeckCritiqueResult,
)
from ppt_creator_ai.providers.heuristic import HeuristicBriefingProvider
from ppt_creator_ai.providers.local_service import LocalServiceBriefingProvider

PROVIDERS: dict[str, BriefingProvider] = {
    HeuristicBriefingProvider.name: HeuristicBriefingProvider(),
    LocalServiceBriefingProvider.name: LocalServiceBriefingProvider(),
}


def list_provider_names() -> list[str]:
    return sorted(PROVIDERS)


def get_provider(name: str) -> BriefingProvider:
    normalized = name.strip().lower().replace("-", "_")
    if normalized in {"service", "local", "hf_local_llm_service"}:
        normalized = LocalServiceBriefingProvider.name
    if normalized not in PROVIDERS:
        raise ValueError(f"Unknown briefing provider: {name}")
    return PROVIDERS[normalized]


__all__ = [
    "BriefingGenerationResult",
    "BriefingProvider",
    "DeckCritiqueResult",
    "HeuristicBriefingProvider",
    "LocalServiceBriefingProvider",
    "PROVIDERS",
    "get_provider",
    "list_provider_names",
]
