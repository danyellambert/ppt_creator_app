from __future__ import annotations

from ppt_creator_ai.providers.anthropic import AnthropicBriefingProvider
from ppt_creator_ai.providers.base import BriefingGenerationResult, BriefingProvider
from ppt_creator_ai.providers.heuristic import HeuristicBriefingProvider
from ppt_creator_ai.providers.local_gguf import PPTAgentLocalProvider
from ppt_creator_ai.providers.ollama import OllamaBriefingProvider
from ppt_creator_ai.providers.openai import OpenAIBriefingProvider

PROVIDERS: dict[str, BriefingProvider] = {
    AnthropicBriefingProvider.name: AnthropicBriefingProvider(),
    HeuristicBriefingProvider.name: HeuristicBriefingProvider(),
    OllamaBriefingProvider.name: OllamaBriefingProvider(),
    OpenAIBriefingProvider.name: OpenAIBriefingProvider(),
    PPTAgentLocalProvider.name: PPTAgentLocalProvider(),
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
    "AnthropicBriefingProvider",
    "HeuristicBriefingProvider",
    "OllamaBriefingProvider",
    "OpenAIBriefingProvider",
    "PPTAgentLocalProvider",
    "PROVIDERS",
    "get_provider",
    "list_provider_names",
]
