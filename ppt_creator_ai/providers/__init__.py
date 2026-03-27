from __future__ import annotations

from ppt_creator_ai.providers.base import BriefingGenerationResult, BriefingProvider
from ppt_creator_ai.providers.heuristic import HeuristicBriefingProvider

PROVIDERS: dict[str, BriefingProvider] = {
    HeuristicBriefingProvider.name: HeuristicBriefingProvider(),
}


def list_provider_names() -> list[str]:
    return sorted(PROVIDERS)


def get_provider(name: str) -> BriefingProvider:
    normalized = name.strip().lower().replace("-", "_")
    if normalized not in PROVIDERS:
        raise ValueError(f"Unknown briefing provider: {name}")
    return PROVIDERS[normalized]


__all__ = [
    "BriefingGenerationResult",
    "BriefingProvider",
    "HeuristicBriefingProvider",
    "PROVIDERS",
    "get_provider",
    "list_provider_names",
]
