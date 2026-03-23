"""Public API for the reusable JSON-to-PPTX creator."""

from ppt_creator.renderer import PresentationRenderer, render_presentation
from ppt_creator.schema import CardItem, MetricItem, PresentationInput, PresentationMeta, Slide, SlideType
from ppt_creator.theme import (
    EXECUTIVE_PREMIUM_MINIMAL,
    CanvasTokens,
    ColorTokens,
    ComponentTokens,
    SpacingTokens,
    Theme,
    TypographyTokens,
    get_theme,
)

__version__ = "0.1.0"

__all__ = [
    "ColorTokens",
    "ComponentTokens",
    "__version__",
    "CardItem",
    "EXECUTIVE_PREMIUM_MINIMAL",
    "MetricItem",
    "PresentationInput",
    "PresentationMeta",
    "PresentationRenderer",
    "SpacingTokens",
    "Slide",
    "TypographyTokens",
    "SlideType",
    "Theme",
    "get_theme",
    "render_presentation",
]
