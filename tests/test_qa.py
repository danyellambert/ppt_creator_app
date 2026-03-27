from __future__ import annotations

from ppt_creator.qa import review_presentation
from ppt_creator.schema import PresentationInput


def test_review_presentation_reports_density_and_balance_signals() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "QA Stress Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "comparison",
                    "title": "Before vs after",
                    "comparison_columns": [
                        {
                            "title": "Before",
                            "body": "This is an intentionally dense narrative block designed to trigger review heuristics because it is significantly longer than the neighboring column and contains too much detail for a compact executive panel.",
                            "bullets": [
                                "A very long bullet that adds even more density to the current-state column.",
                                "Another long bullet that increases the imbalance between columns.",
                                "A third long bullet that pushes the slide closer to overflow risk.",
                            ],
                        },
                        {
                            "title": "After",
                            "bullets": ["Cleaner workflow", "Better visibility"],
                        },
                    ],
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")

    assert review["issue_count"] > 0
    assert review["overflow_risk_count"] >= 1
    assert review["balance_warning_count"] >= 1
    assert review["severity_counts"]["medium"] >= 1


def test_review_presentation_includes_slide_level_risk_metadata() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "QA Metadata Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "image_text",
                    "title": "Image text",
                    "body": "A moderately long narrative paragraph used to exercise slide-level content metadata.",
                    "bullets": [
                        "First supporting bullet with some detail",
                        "Second supporting bullet with additional context",
                    ],
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    slide = review["slides"][0]

    assert "content_weight" in slide
    assert "overflow_risk_count" in slide
    assert "balance_warning_count" in slide
    assert "severity_counts" in slide