from __future__ import annotations

import ppt_creator
from ppt_creator.layouts import LAYOUT_RENDERERS


def test_public_api_exports_expected_symbols() -> None:
    assert ppt_creator.__version__ == "0.1.0"
    assert ppt_creator.PresentationRenderer is not None
    assert ppt_creator.PresentationInput is not None
    assert ppt_creator.SlideType.IMAGE_TEXT.value == "image_text"
    assert ppt_creator.get_theme("Executive Premium Minimal").name == "executive_premium_minimal"
    assert ppt_creator.get_theme("Dark Boardroom").name == "dark_boardroom"
    assert ppt_creator.CONSULTING_CLEAN.name == "consulting_clean"


def test_layout_registry_covers_all_slide_types() -> None:
    assert set(LAYOUT_RENDERERS) == set(ppt_creator.SlideType)


def test_theme_token_groups_are_exposed() -> None:
    theme = ppt_creator.get_theme("executive_premium_minimal")
    assert isinstance(theme.spacing, ppt_creator.SpacingTokens)
    assert isinstance(theme.components, ppt_creator.ComponentTokens)
    assert isinstance(theme.grid, ppt_creator.GridTokens)
    assert theme.grid.content_width > 0


def test_theme_overrides_apply_custom_brand_colors() -> None:
    theme = ppt_creator.get_theme(
        "consulting_clean",
        primary_color="#112233",
        secondary_color="ABCDEF",
    )

    assert theme.colors.navy == "112233"
    assert theme.colors.accent == "ABCDEF"
    assert ppt_creator.theme_display_name(theme.name) == "Consulting Clean"


def test_domain_templates_are_exposed() -> None:
    assert ppt_creator.list_template_domains() == ["consulting", "product", "sales", "strategy"]

    payload = ppt_creator.build_domain_template("sales")
    assert payload["presentation"]["theme"] == "dark_boardroom"
    assert len(payload["slides"]) >= 4
