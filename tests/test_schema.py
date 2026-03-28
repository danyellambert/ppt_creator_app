from __future__ import annotations

import pytest

from ppt_creator.schema import PresentationInput


def test_example_schema_is_valid() -> None:
    spec = PresentationInput.from_path("examples/ai_sales.json")
    assert spec.presentation.title == "AI copilots for sales teams"
    assert len(spec.slides) == 10


def test_cards_requires_exactly_three_cards() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "cards",
                "title": "Bad cards",
                "cards": [
                    {"title": "One", "body": "A"},
                    {"title": "Two", "body": "B"}
                ]
            }
        ]
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_theme_name_is_normalized() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "Executive Premium Minimal"},
        "slides": [
            {
                "type": "title",
                "title": "Hello"
            }
        ]
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.presentation.theme == "executive_premium_minimal"


def test_bullets_slide_rejects_too_many_bullets() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "bullets",
                "title": "Too many bullets",
                "bullets": [
                    "one",
                    "two",
                    "three",
                    "four",
                    "five",
                    "six",
                    "seven"
                ]
            }
        ]
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_layout_variant_is_normalized() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "image_text",
                "title": "Image",
                "body": "Body",
                "layout_variant": "Image Left"
            }
        ]
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.slides[0].layout_variant == "image_left"


def test_title_layout_variant_is_accepted() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "title",
                "title": "Cover",
                "layout_variant": "Hero Cover",
            }
        ],
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.slides[0].layout_variant == "hero_cover"


def test_invalid_layout_variant_is_rejected() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "metrics",
                "title": "KPIs",
                "layout_variant": "image_left",
                "metrics": [{"value": "10%", "label": "lift"}]
            }
        ]
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_timeline_slide_requires_at_least_two_items() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "timeline",
                "title": "Plan",
                "timeline_items": [{"title": "Only one"}],
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_comparison_slide_requires_exactly_two_columns() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "comparison",
                "title": "Compare",
                "comparison_columns": [
                    {"title": "A", "body": "Alpha"},
                ],
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_brand_colors_are_normalized() -> None:
    payload = {
        "presentation": {
            "title": "Deck",
            "theme": "consulting_clean",
            "primary_color": "#112233",
            "secondary_color": "abcDEF",
        },
        "slides": [{"type": "title", "title": "Hello"}],
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.presentation.primary_color == "112233"
    assert spec.presentation.secondary_color == "ABCDEF"


def test_invalid_brand_color_is_rejected() -> None:
    payload = {
        "presentation": {
            "title": "Deck",
            "theme": "executive_premium_minimal",
            "primary_color": "GGHHII",
        },
        "slides": [{"type": "title", "title": "Hello"}],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_agenda_slide_requires_bullets() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [{"type": "agenda", "title": "Agenda"}],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_summary_slide_requires_body_or_bullets() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [{"type": "summary", "title": "Summary"}],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_image_focal_coordinates_are_accepted() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "image_text",
                "title": "Image",
                "body": "Body",
                "image_path": "image.png",
                "image_focal_x": 0.2,
                "image_focal_y": 0.8,
            }
        ],
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.slides[0].image_focal_x == 0.2
    assert spec.slides[0].image_focal_y == 0.8


def test_image_focal_coordinates_must_stay_in_unit_interval() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "image_text",
                "title": "Image",
                "body": "Body",
                "image_path": "image.png",
                "image_focal_x": 1.5,
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_table_slide_requires_columns_and_rows() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [{"type": "table", "title": "Table", "table_columns": ["A", "B"]}],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_chart_slide_requires_categories_and_series_lengths_to_match() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "chart",
                "title": "Chart",
                "chart_categories": ["Q1", "Q2"],
                "chart_series": [{"name": "Revenue", "values": [1.0]}],
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_chart_slide_accepts_layout_variant() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "chart",
                "title": "Chart",
                "layout_variant": "bar",
                "chart_categories": ["Q1", "Q2"],
                "chart_series": [{"name": "Revenue", "values": [1.0, 2.0]}],
            }
        ],
    }

    spec = PresentationInput.model_validate(payload)
    assert spec.slides[0].layout_variant == "bar"


def test_two_column_slide_requires_exactly_two_columns() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "two_column",
                "title": "Narrative",
                "two_column_columns": [{"title": "Only one", "body": "Body"}],
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)


def test_faq_slide_requires_multiple_items() -> None:
    payload = {
        "presentation": {"title": "Deck", "theme": "executive_premium_minimal"},
        "slides": [
            {
                "type": "faq",
                "title": "FAQ",
                "faq_items": [{"title": "Q1", "body": "A1"}],
            }
        ],
    }

    with pytest.raises(Exception):
        PresentationInput.model_validate(payload)
