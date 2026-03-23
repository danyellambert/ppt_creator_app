from __future__ import annotations

import pytest

from ppt_creator.schema import PresentationInput


def test_example_schema_is_valid() -> None:
    spec = PresentationInput.from_path("examples/ai_sales.json")
    assert spec.presentation.title == "AI copilots for sales teams"
    assert len(spec.slides) == 7


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
