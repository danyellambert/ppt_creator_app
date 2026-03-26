"""Public API for the reusable JSON-to-PPTX creator."""

from ppt_creator.api import (
    build_api_server,
    preview_spec_payload,
    render_spec_payload,
    serve_api,
    validate_spec_payload,
)
from ppt_creator.preview import PreviewRenderer, render_previews
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
from ppt_creator.templates import build_domain_template, list_template_domains
from ppt_creator.theme import (
    CONSULTING_CLEAN,
    DARK_BOARDROOM,
    EXECUTIVE_PREMIUM_MINIMAL,
    STARTUP_MINIMAL,
    CanvasTokens,
    ColorTokens,
    ComponentTokens,
    GridTokens,
    SpacingTokens,
    Theme,
    TypographyTokens,
    get_theme,
    theme_display_name,
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
    "CONSULTING_CLEAN",
    "DARK_BOARDROOM",
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
    "STARTUP_MINIMAL",
    "build_api_server",
    "build_domain_template",
    "get_theme",
    "list_template_domains",
    "PreviewRenderer",
    "preview_spec_payload",
    "render_previews",
    "render_spec_payload",
    "render_presentation",
    "serve_api",
    "theme_display_name",
    "validate_spec_payload",
]
