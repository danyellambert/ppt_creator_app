from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.util import Inches

from ppt_creator.preview import PREVIEW_HEIGHT, PREVIEW_WIDTH, PreviewRenderer
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


def test_build_grid_bounds_returns_expected_matrix() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    grid = renderer.build_grid_bounds(
        left=1.0,
        top=2.0,
        width=4.0,
        height=2.0,
        column_regions=[
            {"kind": "left", "min_width": 1.0, "flex": 1.0},
            {"kind": "right", "min_width": 1.0, "flex": 1.0},
        ],
        row_regions=[
            {"kind": "top", "min_height": 0.6, "flex": 1.0},
            {"kind": "bottom", "min_height": 0.6, "flex": 1.0},
        ],
        column_gap=0.1,
        row_gap=0.2,
    )

    assert len(grid) == 2
    assert len(grid[0]) == 2
    left, top, width, height = grid[0][0]
    assert left >= 1.0
    assert top >= 2.0
    assert width > 1.0
    assert height > 0.6


def test_build_columns_returns_expected_bounds() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    columns = renderer.build_columns(left=1.0, width=4.0, gap=0.1, count=3, min_width=0.8)

    assert len(columns) == 3
    assert columns[1][1] >= 0.8


def test_build_weighted_columns_allocates_more_width_to_heavier_content() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    columns = renderer.build_weighted_columns(
        left=1.0,
        width=4.0,
        gap=0.1,
        weights=[1.0, 3.0],
        min_width=1.0,
    )

    assert columns[1][1] > columns[0][1]


def test_build_constrained_columns_respects_fixed_sidebar_width() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    columns = renderer.build_constrained_columns(
        left=1.0,
        width=10.0,
        gap=0.2,
        regions=[
            {"kind": "main", "min_width": 5.0, "target_share": 3.0},
            {"kind": "sidebar", "width": 3.0, "min_width": 3.0},
        ],
    )

    assert len(columns) == 2
    assert columns[1][1] == pytest.approx(3.0)
    assert columns[0][1] == pytest.approx(6.8)


def test_build_panel_row_bounds_returns_rectangles() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    bounds = renderer.build_panel_row_bounds(left=1.0, top=2.0, width=4.0, height=1.5, gap=0.1, count=2, min_width=1.2)

    assert len(bounds) == 2
    assert bounds[0][1] == 2.0
    assert bounds[0][3] == 1.5


def test_build_panel_grid_creates_matrix_from_counts() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    grid = renderer.build_panel_grid(
        left=1.0,
        top=2.0,
        width=4.0,
        height=2.0,
        column_gap=0.1,
        row_gap=0.2,
        column_count=2,
        row_count=2,
        column_min_width=1.0,
        row_min_height=0.6,
    )

    assert len(grid) == 2
    assert len(grid[0]) == 2


def test_build_weighted_rows_allocates_more_height_to_heavier_content() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    rows = renderer.build_weighted_rows(
        top=1.0,
        height=3.0,
        gap=0.1,
        weights=[1.0, 3.0],
        min_height=0.6,
    )

    assert rows[1][1] > rows[0][1]


def test_build_constrained_rows_respects_max_height_caps() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    rows = renderer.build_constrained_rows(
        top=1.0,
        height=4.0,
        gap=0.1,
        regions=[
            {"kind": "intro", "min_height": 0.6, "target_share": 1.0, "max_height": 1.0},
            {"kind": "chart", "min_height": 1.5, "target_share": 3.0},
        ],
    )

    assert rows[0][1] <= 1.0
    assert rows[1][1] > rows[0][1]


def test_build_weighted_panel_grid_allocates_more_space_to_heavier_regions() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    grid = renderer.build_weighted_panel_grid(
        left=1.0,
        top=2.0,
        width=5.0,
        height=3.0,
        column_gap=0.1,
        row_gap=0.2,
        column_weights=[1.0, 2.5],
        row_weights=[1.0, 2.0],
        column_min_width=1.0,
        row_min_height=0.8,
    )

    assert len(grid) == 2
    assert len(grid[0]) == 2
    assert grid[0][1][2] > grid[0][0][2]
    assert grid[1][0][3] > grid[0][0][3]


def test_build_weighted_panel_row_content_bounds_returns_panel_and_inner_bounds() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    bounds = renderer.build_weighted_panel_row_content_bounds(
        left=1.0,
        top=2.0,
        width=5.0,
        height=1.8,
        gap=0.1,
        weights=[1.0, 2.0],
        min_width=1.2,
        padding=0.2,
    )

    assert len(bounds) == 2
    first_panel, first_content = bounds[0]
    assert first_panel[0] == 1.0
    assert first_content[0] == pytest.approx(first_panel[0] + 0.2)


def test_build_panel_grid_content_bounds_returns_panel_and_inner_bounds() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    grid = renderer.build_panel_grid_content_bounds(
        left=1.0,
        top=2.0,
        width=4.0,
        height=2.0,
        column_gap=0.1,
        row_gap=0.1,
        column_count=2,
        row_count=2,
        column_min_width=1.0,
        row_min_height=0.6,
        padding=0.12,
    )

    assert len(grid) == 2
    panel_bounds, content_bounds = grid[0][0]
    assert content_bounds[0] == pytest.approx(panel_bounds[0] + 0.12)


def test_build_panel_content_stack_bounds_uses_inner_padding() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    regions = renderer.build_panel_content_stack_bounds(
        left=1.0,
        top=2.0,
        width=4.0,
        height=2.0,
        padding=0.2,
        regions=[
            {"kind": "title", "height": 0.3},
            {"kind": "body", "min_height": 0.6, "flex": 1.0, "content_weight": 2.0},
        ],
        gap=0.1,
    )

    assert len(regions) == 2
    assert regions[0][1][0] == 1.2
    assert regions[0][1][2] == 3.6


def test_build_constrained_panel_content_stack_bounds_uses_target_share_and_padding() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    regions = renderer.build_constrained_panel_content_stack_bounds(
        left=1.0,
        top=2.0,
        width=4.0,
        height=2.4,
        padding=0.2,
        regions=[
            {"kind": "intro", "min_height": 0.4, "target_share": 1.0, "max_height": 0.8},
            {"kind": "body", "min_height": 0.9, "target_share": 3.0},
        ],
        gap=0.1,
    )

    assert len(regions) == 2
    assert regions[0][1][0] == pytest.approx(1.2)
    assert regions[0][1][2] == pytest.approx(3.6)
    assert regions[0][1][3] <= 0.8


def test_build_constrained_panel_grid_content_bounds_returns_matrix_with_inner_bounds() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    grid = renderer.build_constrained_panel_grid_content_bounds(
        left=1.0,
        top=2.0,
        width=5.2,
        height=3.0,
        column_gap=0.1,
        row_gap=0.2,
        column_regions=[
            {"kind": "left", "min_width": 1.4, "target_share": 1.0, "max_width": 1.8},
            {"kind": "right", "min_width": 1.8, "target_share": 2.0},
        ],
        row_regions=[
            {"kind": "top", "min_height": 0.8, "target_share": 1.0, "max_height": 1.0},
            {"kind": "bottom", "min_height": 1.0, "target_share": 2.0},
        ],
        padding=0.15,
    )

    assert len(grid) == 2
    assert len(grid[0]) == 2
    first_panel, first_content = grid[0][0]
    assert first_content[0] == pytest.approx(first_panel[0] + 0.15)
    assert first_content[1] == pytest.approx(first_panel[1] + 0.15)
    assert first_panel[2] <= 1.8


def test_estimate_content_weight_increases_with_more_content() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    light = renderer.estimate_content_weight(title="Short")
    heavy = renderer.estimate_content_weight(
        title="Longer title for comparison",
        body="This body contains substantially more words and should therefore produce a higher estimated content weight.",
        bullets=["A long bullet explaining more context", "Another long bullet with more detail"],
    )

    assert heavy > light


def test_normalize_content_flexes_returns_scaled_values() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    flexes = renderer.normalize_content_flexes([1.0, 2.0, 3.0], min_flex=0.8, max_flex=1.4)

    assert len(flexes) == 3
    assert min(flexes) >= 0.8
    assert max(flexes) <= 1.4
    assert flexes[0] < flexes[-1]


def test_build_content_stack_allocates_more_height_to_heavier_region() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    regions = renderer.build_content_stack(
        top=1.0,
        height=3.0,
        regions=[
            {"kind": "body", "min_height": 0.6, "flex": 1.0, "content_weight": 1.0},
            {"kind": "bullets", "min_height": 0.6, "flex": 1.0, "content_weight": 3.0},
        ],
        gap=0.1,
        min_flex=0.9,
        max_flex=1.4,
    )

    assert regions[1][1][1] > regions[0][1][1]


def test_compute_cover_crop_crops_wide_images_horizontally() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    crop_left, crop_top, crop_right, crop_bottom = renderer.compute_cover_crop(
        image_width_px=400,
        image_height_px=200,
        box_width=2.0,
        box_height=2.0,
    )

    assert crop_left > 0
    assert crop_right == pytest.approx(crop_left)
    assert crop_top == 0
    assert crop_bottom == 0


def test_compute_cover_crop_crops_tall_images_vertically() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    crop_left, crop_top, crop_right, crop_bottom = renderer.compute_cover_crop(
        image_width_px=200,
        image_height_px=400,
        box_width=2.0,
        box_height=1.0,
    )

    assert crop_top > 0
    assert crop_bottom == pytest.approx(crop_top)
    assert crop_left == 0
    assert crop_right == 0


def test_compute_cover_crop_respects_horizontal_focal_point() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    crop_left, _, crop_right, _ = renderer.compute_cover_crop(
        image_width_px=400,
        image_height_px=200,
        box_width=2.0,
        box_height=2.0,
        focal_x=0.15,
    )

    assert crop_left == pytest.approx(0.0)
    assert crop_right > 0.0


def test_compute_cover_crop_respects_vertical_focal_point() -> None:
    renderer = PresentationRenderer(asset_root="examples")

    _, crop_top, _, crop_bottom = renderer.compute_cover_crop(
        image_width_px=200,
        image_height_px=400,
        box_width=2.0,
        box_height=1.0,
        focal_y=0.85,
    )

    assert crop_bottom < crop_top
    assert crop_bottom >= 0.0
    assert crop_top > 0.0


def test_add_image_cover_applies_crop_for_mismatched_aspect_ratio(tmp_path: Path) -> None:
    image_path = tmp_path / "wide.png"
    Image.new("RGB", (400, 200), (120, 140, 180)).save(image_path)

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    renderer = PresentationRenderer(asset_root="examples")

    picture = renderer.add_image_cover(slide, image_path, left=1.0, top=1.0, width=2.0, height=2.0)

    assert picture.crop_left > 0
    assert picture.crop_right == pytest.approx(picture.crop_left)


def test_preview_artifact_review_flags_body_content_packed_into_corner(tmp_path: Path) -> None:
    renderer = PreviewRenderer()
    image = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), (246, 244, 240))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 64, 64), fill=(20, 30, 40))

    preview_path = tmp_path / "corner-packed.png"
    image.save(preview_path)

    review = renderer.build_preview_artifact_review([str(preview_path)])

    assert review["corner_density_warning_count"] == 1
    assert review["body_edge_contact_count"] == 1
    assert review["slides"][0]["corner_density_warning"] is True


def test_preview_artifact_review_flags_body_content_near_footer_boundary(tmp_path: Path) -> None:
    renderer = PreviewRenderer()
    image = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), (246, 244, 240))
    draw = ImageDraw.Draw(image)
    footer_line_y = renderer._y(renderer.theme.grid.footer_line_y)
    draw.rectangle((220, footer_line_y - 20, 1060, footer_line_y - 4), fill=(20, 30, 40))

    preview_path = tmp_path / "footer-intrusion.png"
    image.save(preview_path)

    review = renderer.build_preview_artifact_review([str(preview_path)])

    assert review["footer_intrusion_count"] == 1
    assert review["slides"][0]["footer_intrusion_warning"] is True


def test_preview_image_text_respects_focal_point_when_cover_cropping(tmp_path: Path) -> None:
    asset_path = tmp_path / "focus.png"
    image = Image.new("RGB", (400, 200), (0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 199, 199), fill=(255, 0, 0))
    image.save(asset_path)

    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "image_text",
                    "title": "Focused image",
                    "body": "Body",
                    "image_path": str(asset_path),
                    "image_focal_x": 0.15,
                }
            ],
        }
    )

    renderer = PreviewRenderer(asset_root=tmp_path)
    rendered = renderer.render_slide(spec.presentation, spec.slides[0], 1, 1)

    sampled = rendered.getpixel((974, 370))
    assert sampled[0] > sampled[2]


def test_preview_title_hero_cover_respects_focal_point_when_image_present(tmp_path: Path) -> None:
    asset_path = tmp_path / "title_focus.png"
    image = Image.new("RGB", (400, 200), (0, 0, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 199, 199), fill=(255, 0, 0))
    image.save(asset_path)

    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "title",
                    "title": "Focused cover",
                    "layout_variant": "hero_cover",
                    "image_path": str(asset_path),
                    "image_focal_x": 0.15,
                }
            ],
        }
    )

    renderer = PreviewRenderer(asset_root=tmp_path)
    rendered = renderer.render_slide(spec.presentation, spec.slides[0], 1, 1)

    sampled = rendered.getpixel((960, 230))
    assert sampled[0] > sampled[2]


def test_title_layout_with_cover_image_renders_without_crashing(tmp_path: Path) -> None:
    asset_path = tmp_path / "title_cover.png"
    Image.new("RGB", (400, 200), (120, 140, 180)).save(asset_path)
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "title",
                    "title": "Cover with image",
                    "layout_variant": "hero_cover",
                    "image_path": str(asset_path),
                }
            ],
        }
    )
    output = tmp_path / "title-cover-image.pptx"

    renderer = PresentationRenderer(asset_root=tmp_path)
    rendered = renderer.render(spec, output)

    assert rendered.exists()
