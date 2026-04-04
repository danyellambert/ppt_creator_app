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


def test_review_presentation_reports_summary_takeaway_and_split_pressure() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Summary QA Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "summary",
                    "title": "Executive summary",
                    "body": "This summary narrative is intentionally dense and verbose so the split between narrative and takeaways has a clear chance to feel imbalanced and crowded in the available space.",
                    "bullets": [
                        "A long takeaway that keeps adding qualifiers until the row becomes structurally risky for the compact panel.",
                        "A second long takeaway that adds more weight and pushes the takeaways stack toward clipping risk.",
                        "A third dense takeaway with enough wording to stress the panel and force more visible pressure signals.",
                    ],
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    slide = review["slides"][0]

    assert any(region.startswith("summary:takeaway_") for region in slide["likely_collision_regions"])
    assert "summary:takeaways" in slide["likely_collision_regions"]


def test_review_presentation_separates_comparison_and_two_column_pressure_regions() -> None:
    long_comparison_bullet = (
        "A deliberately long supporting bullet that adds enough explanatory detail to create real row-level pressure "
        "inside a compact executive comparison panel."
    )
    long_two_column_bullet = (
        "A deliberately long narrative bullet that should become dense enough to trigger row-level clipping pressure "
        "inside the two-column panel."
    )
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Column QA Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "comparison",
                    "title": "Comparison",
                    "comparison_columns": [
                        {
                            "title": "Current state",
                            "body": "This intentionally dense comparison narrative forces the first comparison panel to carry much more detail than the second one.",
                            "bullets": [
                                long_comparison_bullet,
                                long_comparison_bullet,
                            ],
                        },
                        {"title": "Target state", "bullets": ["Cleaner flow"]},
                    ],
                },
                {
                    "type": "two_column",
                    "title": "Two column",
                    "two_column_columns": [
                        {
                            "title": "Narrative left",
                            "body": "This left-hand narrative is intentionally verbose so the two-column panel gets its own body pressure signal.",
                            "bullets": [long_two_column_bullet, long_two_column_bullet],
                        },
                        {"title": "Narrative right", "body": "Short body"},
                    ],
                },
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    comparison_slide = review["slides"][0]
    two_column_slide = review["slides"][1]

    assert any(region.startswith("comparison:") for region in comparison_slide["likely_collision_regions"])
    assert any(region.startswith("two_column:") for region in two_column_slide["likely_collision_regions"])
    assert any(region.startswith("comparison:column_1:bullet_") for region in comparison_slide["likely_collision_regions"])
    assert any(region.startswith("two_column:column_1:bullet_") for region in two_column_slide["likely_collision_regions"])


def test_review_presentation_reports_metrics_faq_and_table_pressure_regions() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Layout QA Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "metrics",
                    "title": "Metrics",
                    "metrics": [
                        {"label": "Pipeline coverage", "value": "3.2x", "detail": "This detail is intentionally long so the card becomes dense and harder to balance cleanly.", "trend": "+18%"},
                        {"label": "Win rate", "value": "29%", "detail": "Another detail field with enough text to create pressure inside the card.", "trend": "+4 pts"},
                        {"label": "Cycle time", "value": "41d", "detail": "Shorter detail"},
                    ],
                },
                {
                    "type": "faq",
                    "title": "FAQ",
                    "faq_items": [
                        {"title": "Why now?", "body": "A deliberately long FAQ answer that adds enough narrative density to create cramped panel composition and a stronger pressure signal."},
                        {"title": "How do we scale?", "body": "Another long FAQ answer with too much context for a compact answer box in a four-panel layout."},
                        {"title": "What do we measure?", "body": "Success metrics, adoption signals and quality lift over time."},
                        {"title": "What is the risk?", "body": "Operational inconsistency if the rollout is not constrained."},
                    ],
                },
                {
                    "type": "table",
                    "title": "Table",
                    "table_columns": [
                        "Workstream and operating scope",
                        "Executive owner and sponsor",
                        "Decision required this cycle",
                        "Current status and implication",
                    ],
                    "table_rows": [
                        ["Revenue operations redesign with additional qualifiers", "Executive sponsor with long title", "Approve the pilot scope with multiple gates", "Needs alignment"],
                        ["Enablement rollout", "Regional sales leader", "Sequence onboarding, measurement and governance", "In progress"],
                        ["Inspection cadence", "Chief of staff", "Formalize metrics, reporting and weekly readouts", "At risk"],
                    ],
                },
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    metrics_slide = review["slides"][0]
    faq_slide = review["slides"][1]
    table_slide = review["slides"][2]

    assert any(region.startswith("metrics:") for region in metrics_slide["likely_collision_regions"])
    assert any(region.startswith("faq:") for region in faq_slide["likely_collision_regions"])
    assert any(region.startswith("faq:item_1:") for region in faq_slide["likely_collision_regions"])
    assert any(region.startswith("table:column_") for region in table_slide["likely_collision_regions"])
    assert any(region.startswith("table:row_") for region in table_slide["likely_collision_regions"])
    assert any(region.startswith("table:header_") for region in table_slide["likely_collision_regions"])


def test_review_presentation_reports_closing_pressure_regions() -> None:
    spec = PresentationInput.model_validate(
        {
            "presentation": {"title": "Closing QA Deck", "theme": "executive_premium_minimal"},
            "slides": [
                {
                    "type": "closing",
                    "title": "Closing",
                    "quote": "This closing quote is intentionally long and densely written so the quote block and the side action panel both have a realistic chance to become visually cramped in the final composition.",
                    "attribution": "Executive sponsor with a deliberately long attribution line",
                }
            ],
        }
    )

    review = review_presentation(spec, asset_root="examples")
    slide = review["slides"][0]

    assert any(region.startswith("closing:") for region in slide["likely_collision_regions"])
    assert any(region in slide["likely_collision_regions"] for region in ["closing:quote", "closing:attribution", "closing:panel"])