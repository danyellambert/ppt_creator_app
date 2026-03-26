"""Optional briefing-to-deck generation layer kept separate from the core renderer."""

from ppt_creator_ai.briefing import (
    BriefingFAQ,
    BriefingInput,
    BriefingMetric,
    BriefingMilestone,
    BriefingOption,
    generate_presentation_input_from_briefing,
    generate_presentation_payload_from_briefing,
)

__all__ = [
    "BriefingFAQ",
    "BriefingInput",
    "BriefingMetric",
    "BriefingMilestone",
    "BriefingOption",
    "generate_presentation_input_from_briefing",
    "generate_presentation_payload_from_briefing",
]
