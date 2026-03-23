"""Public API for the reusable JSON-to-PPTX creator."""

from ppt_creator.renderer import PresentationRenderer, render_presentation
from ppt_creator.schema import CardItem, MetricItem, PresentationInput, PresentationMeta, Slide, SlideType
from ppt_creator.theme import EXECUTIVE_PREMIUM_MINIMAL, Theme, get_theme

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CardItem",
    "EXECUTIVE_PREMIUM_MINIMAL",
    "MetricItem",
    "PresentationInput",
    "PresentationMeta",
    "PresentationRenderer",
    "Slide",
    "SlideType",
    "Theme",
    "get_theme",
    "render_presentation",
]
