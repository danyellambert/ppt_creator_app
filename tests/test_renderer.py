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
    assert len(presentation.slides) == 10


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


def test_fit_text_frame_reduces_font_size_for_tight_box() -> None:
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    renderer = PresentationRenderer(asset_root="examples")

    shape = renderer.textbox(slide, 1.0, 1.0, 2.4, 0.45)
    renderer.write_paragraph(
        shape.text_frame,
        "This is a deliberately long title that should shrink to fit the box.",
        size=28,
        color=renderer.theme.colors.navy,
        bold=True,
    )
    renderer.fit_text_frame(shape.text_frame, max_size=28, bold=True)

    run = shape.text_frame.paragraphs[0].runs[0]
    assert run.font.size is not None
    assert run.font.size.pt <= 28


def test_stack_vertical_regions_distributes_flexible_space() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    regions = renderer.stack_vertical_regions(
        top=1.0,
        height=2.0,
        regions=[
            {"kind": "title", "height": 0.3},
            {"kind": "body", "min_height": 0.4, "flex": 1.0},
            {"kind": "footer", "height": 0.2},
        ],
        gap=0.1,
    )

    assert len(regions) == 3
    body_bounds = regions[1][1]
    assert body_bounds[1] > 0.4


def test_stack_horizontal_regions_distributes_flexible_space() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    regions = renderer.stack_horizontal_regions(
        left=1.0,
        width=4.0,
        regions=[
            {"kind": "left", "width": 0.8},
            {"kind": "center", "min_width": 0.8, "flex": 1.0},
            {"kind": "right", "width": 0.8},
        ],
        gap=0.1,
    )

    assert len(regions) == 3
    center_bounds = regions[1][1]
    assert center_bounds[1] > 0.8
