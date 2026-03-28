from __future__ import annotations

from ppt_creator.qa import (
    augment_review_with_preview_artifacts,
    review_presentation,
    review_preview_artifacts,
)
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
    assert review["clipping_risk_count"] >= 1
    assert review["collision_risk_count"] >= 1
    assert review["severity_counts"]["medium"] >= 1
    assert review["top_risk_slides"]


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
    assert "clipping_risk_count" in slide
    assert "collision_risk_count" in slide
    assert "balance_warning_count" in slide
    assert "layout_pressure_score" in slide
    assert "severity_counts" in slide
    assert "risk_level" in slide
    assert "likely_overflow_regions" in slide
    assert "likely_collision_regions" in slide


def test_review_presentation_reports_layout_pressure_for_agenda_rows() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Agenda Pressure Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "agenda",
                    "title": "Agenda",
                    "body": "This introduction is intentionally dense so the agenda intro plus rows produce stronger layout-pressure signals.",
                    "bullets": [
                        "A very long agenda row that keeps adding qualifiers and detail until it becomes visually risky for the available row height.",
                        "Another verbose agenda row with too much nuance for a compact executive agenda row.",
                        "A third dense agenda row that should reinforce collision-style pressure detection.",
                        "A fourth row with enough wording to stress the available space.",
                    ],
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")

    assert review["collision_risk_count"] >= 1
    assert review["slides"][0]["likely_collision_regions"]


def test_augment_review_with_preview_artifacts_adds_final_preview_clipping_and_collision_signals() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Preview QA Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "summary",
                    "title": "Executive summary",
                    "bullets": ["Keep the workflow tight", "Measure adoption", "Scale with discipline"],
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    augmented = augment_review_with_preview_artifacts(
        review,
        {
            "preview_artifact_review": {
                "status": "review",
                "slides": [
                    {
                        "slide_number": 1,
                        "edge_contact": False,
                        "safe_margin_warning": False,
                        "body_edge_contact": True,
                        "safe_area_intrusion": True,
                        "footer_intrusion_warning": True,
                        "edge_density_warning": True,
                        "corner_density_warning": True,
                    }
                ],
            }
        },
    )

    assert augmented["clipping_risk_count"] > review["clipping_risk_count"]
    assert augmented["collision_risk_count"] > review["collision_risk_count"]
    assert any("final preview" in issue for issue in augmented["issues"])


def test_review_preview_artifacts_builds_review_summary_from_rendered_preview_only() -> None:
    review = review_preview_artifacts(
        {
            "input_pptx": "outputs/sample.pptx",
            "preview_count": 2,
            "preview_artifact_review": {
                "slides": [
                    {
                        "slide_number": 1,
                        "edge_contact": True,
                        "safe_margin_warning": False,
                        "body_edge_contact": True,
                        "safe_area_intrusion": False,
                        "footer_intrusion_warning": False,
                        "edge_density_warning": True,
                        "corner_density_warning": False,
                        "body_max_edge_ratio": 0.08,
                        "max_corner_ratio": 0.01,
                    },
                    {
                        "slide_number": 2,
                        "edge_contact": False,
                        "safe_margin_warning": True,
                        "body_edge_contact": False,
                        "safe_area_intrusion": False,
                        "footer_intrusion_warning": True,
                        "edge_density_warning": False,
                        "corner_density_warning": True,
                        "body_max_edge_ratio": 0.02,
                        "max_corner_ratio": 0.07,
                    },
                ]
            },
            "visual_regression": {
                "diff_count": 1,
                "slides": [{"slide_number": 2, "regression": True}],
            },
        }
    )

    assert review["issue_count"] >= 4
    assert review["collision_risk_count"] >= 3
    assert review["clipping_risk_count"] >= 2
    assert review["regression_diff_count"] == 1