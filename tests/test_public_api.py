from __future__ import annotations

import ppt_creator
from ppt_creator.layouts import LAYOUT_RENDERERS


def test_public_api_exports_expected_symbols() -> None:
    assert ppt_creator.__version__ == "0.1.0"
    assert ppt_creator.PresentationRenderer is not None
    assert ppt_creator.PresentationInput is not None
    assert ppt_creator.SlideType.IMAGE_TEXT.value == "image_text"
    assert ppt_creator.get_theme("Executive Premium Minimal").name == "executive_premium_minimal"
    assert ppt_creator.get_theme("Dark Boardroom").name == "dark_boardroom"
    assert ppt_creator.CONSULTING_CLEAN.name == "consulting_clean"


def test_layout_registry_covers_all_slide_types() -> None:
    assert set(LAYOUT_RENDERERS) == set(ppt_creator.SlideType)


def test_theme_token_groups_are_exposed() -> None:
    theme = ppt_creator.get_theme("executive_premium_minimal")
    assert isinstance(theme.spacing, ppt_creator.SpacingTokens)
    assert isinstance(theme.components, ppt_creator.ComponentTokens)
    assert isinstance(theme.grid, ppt_creator.GridTokens)
    assert isinstance(theme.semantic, ppt_creator.SemanticLayoutTokens)
    assert theme.grid.content_width > 0


def test_theme_overrides_apply_custom_brand_colors() -> None:
    theme = ppt_creator.get_theme(
        "consulting_clean",
        primary_color="#112233",
        secondary_color="ABCDEF",
    )

    assert theme.colors.navy == "112233"
    assert theme.colors.accent == "ABCDEF"
    assert ppt_creator.theme_display_name(theme.name) == "Consulting Clean"


def test_domain_templates_are_exposed() -> None:
    assert ppt_creator.list_template_domains() == ["consulting", "product", "proposal", "sales", "strategy"]
    assert ppt_creator.list_brand_packs() == ["board_navy", "consulting_signature", "product_signal", "sales_pipeline"]
    assert ppt_creator.list_themes() == [
        "consulting_clean",
        "dark_boardroom",
        "executive_premium_minimal",
        "startup_minimal",
    ]

    payload = ppt_creator.build_domain_template("sales")
    assert payload["presentation"]["theme"] == "dark_boardroom"
    assert len(payload["slides"]) >= 4

    proposal_payload = ppt_creator.build_domain_template("proposal", audience_profile="proposal")
    assert proposal_payload["presentation"]["title"] == "Commercial proposal"
    assert proposal_payload["presentation"]["footer_text"] == "Proposal profile"

    packet = ppt_creator.build_template_packet("sales", brand_pack="sales_pipeline")
    assert packet["asset_collections"]
    assert packet["asset_strategy"]["placeholder_style"] == "analytical_visual"
    assert packet["asset_strategy"]["logo_text"] == "SALES PIPELINE"
    assert packet["branding_bundle"]["logo_text"] == "SALES PIPELINE"
    assert packet["slide_asset_suggestions"]

    workflow_packet = ppt_creator.build_workflow_packet("sales_qbr")
    assert workflow_packet["slide_asset_suggestions"]
    assert workflow_packet["asset_strategy"]["workflow_name"] == "sales_qbr"
    assert workflow_packet["branding_bundle"]["logo_text"] == "SALES PIPELINE"

    proposal_workflow_packet = ppt_creator.build_workflow_packet("commercial_proposal")
    assert proposal_workflow_packet["workflow"]["domain"] == "proposal"
    assert proposal_workflow_packet["template"]["presentation"]["title"] == "Commercial proposal"

    profiled_payload = ppt_creator.build_domain_template("sales", audience_profile="board")
    assert profiled_payload["presentation"]["footer_text"] == "Board profile"

    branded_payload = ppt_creator.build_domain_template("sales", brand_pack="sales_pipeline")
    assert branded_payload["presentation"]["footer_text"] == "Sales pipeline brand pack"
    assert branded_payload["presentation"]["logo_text"] == "SALES PIPELINE"
    assert branded_payload["slides"][0]["eyebrow"] == "Revenue review"

    marketplace = ppt_creator.build_marketplace_catalog()
    assert marketplace["summary"]["workflow_count"] >= 5
    assert any(item["name"] == "commercial_proposal" for item in marketplace["workflows"])
    assert any(item["name"] == "executive_premium_minimal" for item in marketplace["themes"])
    assert any(item["type"] == "comparison" for item in marketplace["layouts"])


def test_api_helpers_are_exposed() -> None:
    assert ppt_creator.build_api_server is not None
    assert ppt_creator.compare_pptx_artifacts is not None
    assert ppt_creator.compare_pptx_payload is not None
    assert ppt_creator.generate_briefing_payload is not None
    assert ppt_creator.get_asset_collection is not None
    assert ppt_creator.get_audience_profile is not None
    assert ppt_creator.list_asset_collections is not None
    assert ppt_creator.list_audience_profiles is not None
    assert ppt_creator.list_workflow_presets is not None
    assert ppt_creator.PreviewRenderer is not None
    assert ppt_creator.preview_spec_payload is not None
    assert ppt_creator.render_previews is not None
    assert ppt_creator.review_pptx_artifact is not None
    assert ppt_creator.review_preview_artifacts is not None
    assert ppt_creator.review_presentation is not None
    assert ppt_creator.review_spec_payload is not None
    assert ppt_creator.get_workflow_preset is not None
    assert ppt_creator.build_workflow_packet is not None
    assert ppt_creator.serve_api is not None
    assert ppt_creator.validate_spec_payload is not None
    assert ppt_creator.render_spec_payload is not None
