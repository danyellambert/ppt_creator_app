from __future__ import annotations

from copy import deepcopy

from ppt_creator.assets import get_asset_collection
from ppt_creator.profiles import get_audience_profile
from ppt_creator.templates import build_domain_template

WORKFLOW_PRESETS: dict[str, dict[str, object]] = {
    "sales_qbr": {
        "display_name": "Sales QBR",
        "domain": "sales",
        "audience_profile": "sales",
        "description": "Quarterly business review for commercial leadership with KPI, forecast, and execution framing.",
        "operating_mode": "commercial",
        "cadence": "quarterly",
        "stakeholders": ["CRO", "VP Sales", "Revenue Operations"],
        "recommended_asset_collections": ["sales_dashboards", "forecast_reviews"],
        "default_preview_backend": "office",
        "default_output_pptx": "outputs/sales_qbr.pptx",
        "default_preview_dir": "outputs/sales_qbr_previews",
        "default_report_json": "outputs/sales_qbr_report.json",
        "suggested_steps": ["template", "review", "render", "review-pptx"],
    },
    "board_strategy": {
        "display_name": "Board Strategy Review",
        "domain": "strategy",
        "audience_profile": "board",
        "description": "Board-facing strategy review focused on trade-offs, sequencing, and decision clarity.",
        "operating_mode": "board",
        "cadence": "quarterly",
        "stakeholders": ["Board", "CEO", "Strategy Office"],
        "recommended_asset_collections": ["boardroom_backdrops", "executive_decision_moments"],
        "default_preview_backend": "office",
        "default_output_pptx": "outputs/board_strategy_review.pptx",
        "default_preview_dir": "outputs/board_strategy_review_previews",
        "default_report_json": "outputs/board_strategy_review_report.json",
        "suggested_steps": ["template", "review", "render", "compare-pptx"],
    },
    "product_operating_review": {
        "display_name": "Product Operating Review",
        "domain": "product",
        "audience_profile": "product",
        "description": "Operating review for roadmap, adoption, and portfolio decisions across product leadership.",
        "operating_mode": "product",
        "cadence": "monthly",
        "stakeholders": ["CPO", "Product Directors", "Design", "Engineering"],
        "recommended_asset_collections": ["product_mockups", "roadmap_workshops"],
        "default_preview_backend": "auto",
        "default_output_pptx": "outputs/product_operating_review.pptx",
        "default_preview_dir": "outputs/product_operating_review_previews",
        "default_report_json": "outputs/product_operating_review_report.json",
        "suggested_steps": ["template", "review", "preview", "render"],
    },
    "consulting_steerco": {
        "display_name": "Consulting SteerCo",
        "domain": "consulting",
        "audience_profile": "consulting",
        "description": "Client steerco packet for consulting engagements with synthesis, options, and recommendation framing.",
        "operating_mode": "client_service",
        "cadence": "monthly",
        "stakeholders": ["Engagement Lead", "Client Sponsor", "PMO"],
        "recommended_asset_collections": ["strategy_workshops", "team_alignment_sessions"],
        "default_preview_backend": "office",
        "default_output_pptx": "outputs/consulting_steerco.pptx",
        "default_preview_dir": "outputs/consulting_steerco_previews",
        "default_report_json": "outputs/consulting_steerco_report.json",
        "suggested_steps": ["template", "review", "render", "review-pptx"],
    },
}


def list_workflow_presets() -> list[str]:
    return sorted(WORKFLOW_PRESETS)


def get_workflow_preset(name: str) -> dict[str, object]:
    normalized = name.strip().lower().replace("-", "_")
    if normalized not in WORKFLOW_PRESETS:
        raise ValueError(f"Unknown workflow preset: {name}")
    preset = deepcopy(WORKFLOW_PRESETS[normalized])
    preset["name"] = normalized
    return preset


def build_workflow_packet(name: str, *, theme_name: str | None = None) -> dict[str, object]:
    workflow = get_workflow_preset(name)
    audience_profile_name = str(workflow["audience_profile"])
    domain = str(workflow["domain"])
    recommended_asset_collections = [
        get_asset_collection(collection_name)
        for collection_name in workflow.get("recommended_asset_collections", [])
    ]
    return {
        "workflow": workflow,
        "audience_profile": get_audience_profile(audience_profile_name),
        "asset_collections": recommended_asset_collections,
        "template": build_domain_template(
            domain,
            theme_name=theme_name,
            audience_profile=audience_profile_name,
        ),
    }