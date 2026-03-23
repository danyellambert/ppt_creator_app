from __future__ import annotations

import ppt_creator

from ppt_creator.layouts import LAYOUT_RENDERERS


def test_public_api_exports_expected_symbols() -> None:
    assert ppt_creator.__version__ == "0.1.0"
    assert ppt_creator.PresentationRenderer is not None
    assert ppt_creator.PresentationInput is not None
    assert ppt_creator.SlideType.IMAGE_TEXT.value == "image_text"
    assert ppt_creator.get_theme("Executive Premium Minimal").name == "executive_premium_minimal"


def test_layout_registry_covers_all_slide_types() -> None:
    assert set(LAYOUT_RENDERERS) == set(ppt_creator.SlideType)
