from __future__ import annotations

from pathlib import Path

from pptx import Presentation

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


def build_layout_smoke_spec() -> PresentationInput:
    return PresentationInput.model_validate(
        {
            "presentation": {
                "title": "Layout Smoke Test",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {
                    "type": "title",
                    "title": "Title Slide",
                    "subtitle": "Smoke coverage",
                },
                {
                    "type": "section",
                    "title": "Section Slide",
                    "section_label": "Section",
                },
                {
                    "type": "bullets",
                    "title": "Bullets Slide",
                    "bullets": ["One", "Two", "Three"],
                },
                {
                    "type": "cards",
                    "title": "Cards Slide",
                    "cards": [
                        {"title": "Card 1", "body": "Body 1"},
                        {"title": "Card 2", "body": "Body 2"},
                        {"title": "Card 3", "body": "Body 3"},
                    ],
                },
                {
                    "type": "metrics",
                    "title": "Metrics Slide",
                    "metrics": [
                        {"value": "10%", "label": "lift"},
                        {"value": "2x", "label": "speed"},
                    ],
                },
                {
                    "type": "image_text",
                    "title": "Image Slide",
                    "body": "Body copy",
                    "image_path": "missing-image.png",
                    "image_caption": "Placeholder caption",
                },
                {
                    "type": "timeline",
                    "title": "Timeline Slide",
                    "timeline_items": [
                        {"title": "Discover", "body": "Frame the problem", "tag": "Week 1"},
                        {"title": "Pilot", "body": "Run the first workflow", "tag": "Week 2"},
                        {"title": "Scale", "body": "Operationalize the rollout", "tag": "Week 3"},
                    ],
                },
                {
                    "type": "comparison",
                    "title": "Comparison Slide",
                    "comparison_columns": [
                        {
                            "title": "Current state",
                            "body": "Inconsistent execution and fragmented tooling.",
                        },
                        {
                            "title": "Target state",
                            "bullets": ["Clear workflow", "Structured outputs", "Measurable lift"],
                        },
                    ],
                },
                {
                    "type": "closing",
                    "title": "Closing Slide",
                    "quote": "Stay structured.",
                },
            ],
        }
    )


def test_all_layouts_render_without_crashing(tmp_path: Path) -> None:
    spec = build_layout_smoke_spec()
    output = tmp_path / "layouts-smoke.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)

    assert rendered.exists()
    presentation = Presentation(str(rendered))
    assert len(presentation.slides) == 9


def test_missing_image_uses_placeholder_text(tmp_path: Path) -> None:
    spec = build_layout_smoke_spec()
    output = tmp_path / "layouts-placeholder.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)
    presentation = Presentation(str(rendered))

    image_slide = presentation.slides[5]
    texts = [shape.text for shape in image_slide.shapes if hasattr(shape, "text")]
    joined = "\n".join(texts)

    assert "Image unavailable" in joined
    assert "Missing asset: missing-image.png" in joined


def test_layout_variants_render_without_crashing(tmp_path: Path) -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {
                "title": "Variant Deck",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {
                    "type": "bullets",
                    "title": "Full Width Bullets",
                    "layout_variant": "full_width",
                    "bullets": ["One", "Two", "Three"],
                },
                {
                    "type": "metrics",
                    "title": "Compact KPIs",
                    "layout_variant": "compact",
                    "metrics": [
                        {"value": "10%", "label": "lift"},
                        {"value": "2x", "label": "speed"},
                        {"value": "98%", "label": "quality"},
                        {"value": "4h", "label": "saved"},
                    ],
                },
                {
                    "type": "image_text",
                    "title": "Image Left",
                    "layout_variant": "image_left",
                    "body": "Body copy",
                    "image_path": "missing-image.png",
                },
            ],
        }
    )
    output = tmp_path / "variant-layouts.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)

    assert rendered.exists()
    presentation = Presentation(str(rendered))
    assert len(presentation.slides) == 3


def test_new_layout_types_render_without_crashing(tmp_path: Path) -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {
                "title": "New Layout Deck",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {
                    "type": "timeline",
                    "title": "Rollout timeline",
                    "timeline_items": [
                        {"title": "Diagnose", "body": "Find the highest-value workflow"},
                        {"title": "Deploy", "body": "Launch a controlled pilot"},
                        {"title": "Measure", "body": "Track adoption and impact"},
                    ],
                },
                {
                    "type": "comparison",
                    "title": "Before vs after",
                    "comparison_columns": [
                        {
                            "title": "Before",
                            "bullets": ["Manual prep", "Uneven quality"],
                        },
                        {
                            "title": "After",
                            "bullets": ["Structured workflow", "Better consistency"],
                        },
                    ],
                },
            ],
        }
    )
    output = tmp_path / "new-layouts.pptx"

    renderer = PresentationRenderer(asset_root="examples")
    rendered = renderer.render(spec, output)

    assert rendered.exists()
    presentation = Presentation(str(rendered))
    assert len(presentation.slides) == 2
