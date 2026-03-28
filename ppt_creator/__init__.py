"""Public API for the reusable JSON-to-PPTX creator."""

from ppt_creator.api import (
    build_api_server,
    compare_pptx_payload,
    preview_spec_payload,
    render_spec_payload,
    review_spec_payload,
    serve_api,
    validate_spec_payload,
)
from ppt_creator.assets import get_asset_collection, list_asset_collections
from ppt_creator.preview import PreviewRenderer, compare_pptx_artifacts, render_previews
from ppt_creator.profiles import get_audience_profile, list_audience_profiles
from ppt_creator.qa import review_presentation
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
    "compare_pptx_artifacts",
    "compare_pptx_payload",
    "build_domain_template",
    "get_asset_collection",
    "get_audience_profile",
    "get_theme",
    "list_asset_collections",
    "list_audience_profiles",
    "list_template_domains",
    "PreviewRenderer",
    "preview_spec_payload",
    "render_previews",
    "review_presentation",
    "review_spec_payload",
    "render_spec_payload",
    "render_presentation",
    "serve_api",
    "theme_display_name",
    "validate_spec_payload",
]
