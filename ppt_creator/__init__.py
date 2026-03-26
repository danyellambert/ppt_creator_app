"""Public API for the reusable JSON-to-PPTX creator."""

from ppt_creator.renderer import PresentationRenderer, render_presentation
from ppt_creator.schema import (
    CardItem,
    ComparisonColumn,
    MetricItem,
    PresentationInput,
    PresentationMeta,
    Slide,
    SlideType,
    TimelineItem,
)
from ppt_creator.theme import (
    EXECUTIVE_PREMIUM_MINIMAL,
    CanvasTokens,
    ColorTokens,
    ComponentTokens,
    GridTokens,
    SpacingTokens,
    Theme,
    TypographyTokens,
    get_theme,
)

__version__ = "0.1.0"

__all__ = [
    "CanvasTokens",
    "ColorTokens",
    "ComponentTokens",
    "GridTokens",
    "__version__",
    "CardItem",
    "ComparisonColumn",
    "EXECUTIVE_PREMIUM_MINIMAL",
    "MetricItem",
    "PresentationInput",
    "PresentationMeta",
    "PresentationRenderer",
    "SpacingTokens",
    "Slide",
    "SlideType",
    "Theme",
    "TimelineItem",
    "TypographyTokens",
    "get_theme",
    "render_presentation",
]
