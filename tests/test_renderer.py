from __future__ import annotations

from pathlib import Path

import pytest
from pptx import Presentation
from pptx.util import Inches

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


def test_render_example_creates_pptx(tmp_path: Path) -> None:
    spec = PresentationInput.from_path("examples/ai_sales.json")
    output = tmp_path / "example.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)

    assert rendered.exists()
    presentation = Presentation(str(rendered))
    assert len(presentation.slides) == 7


def test_renderer_requires_pptx_output_extension(tmp_path: Path) -> None:
    spec = PresentationInput.from_path("examples/ai_sales.json")
    renderer = PresentationRenderer(asset_root="examples")

    with pytest.raises(ValueError):
        renderer.render(spec, tmp_path / "example.txt")


def test_panel_content_box_uses_theme_padding() -> None:
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    renderer = PresentationRenderer(asset_root="examples")

    box = renderer.panel_content_box(slide, left=1.0, top=1.0, width=4.0, height=2.0)
    padding = renderer.theme.components.panel_padding

    assert box.left == Inches(1.0 + padding)
    assert box.width == Inches(4.0 - (padding * 2))


def test_collect_missing_assets_reports_missing_image() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "image_text",
                    "title": "Image",
                    "body": "Body",
                    "image_path": "missing-image.png",
                }
            ],
        }
    )
    renderer = PresentationRenderer(asset_root="examples")

    missing_assets = renderer.collect_missing_assets(spec)

    assert missing_assets == ["slide 01 (Image): missing asset 'missing-image.png'"]


def test_collect_missing_assets_reports_missing_brand_logo() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {
                "title": "Deck",
                "theme": "executive_premium_minimal",
                "logo_path": "missing-logo.png",
            },
            "slides": [{"type": "title", "title": "Hello"}],
        }
    )
    renderer = PresentationRenderer(asset_root="examples")

    missing_assets = renderer.collect_missing_assets(spec)

    assert missing_assets == ["presentation branding: missing asset 'missing-logo.png'"]
