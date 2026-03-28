from __future__ import annotations

from copy import deepcopy

ASSET_COLLECTIONS: dict[str, dict[str, object]] = {
    "boardroom_backdrops": {
        "description": "Premium boardroom and leadership-meeting visuals suited to title/summary slides.",
        "queries": [
            "executive boardroom meeting wide shot",
            "premium leadership discussion background",
            "decision meeting with negative space",
        ],
        "preferred_layouts": ["title", "summary"],
        "recommended_profiles": ["board", "consulting"],
    },
    "executive_decision_moments": {
        "description": "Crisp decision-oriented visuals for recommendation, summary, and closing frames.",
        "queries": [
            "executive decision moment meeting",
            "leadership alignment summary visual",
            "final recommendation boardroom scene",
        ],
        "preferred_layouts": ["summary", "closing", "comparison"],
        "recommended_profiles": ["board", "consulting", "sales"],
    },
    "sales_dashboards": {
        "description": "Revenue, forecast, and pipeline visuals for metrics/chart-heavy commercial decks.",
        "queries": [
            "sales dashboard pipeline review",
            "forecast review leadership meeting",
            "executive revenue KPI dashboard",
        ],
        "preferred_layouts": ["metrics", "chart", "summary"],
        "recommended_profiles": ["sales"],
    },
    "forecast_reviews": {
        "description": "Commercial review imagery centered on weekly/quarterly forecast execution.",
        "queries": [
            "sales forecast review meeting",
            "pipeline governance workshop",
            "revenue operations meeting",
        ],
        "preferred_layouts": ["agenda", "comparison", "summary"],
        "recommended_profiles": ["sales"],
    },
    "product_mockups": {
        "description": "Product UI, app mockup, and digital-workflow imagery for product roadmap decks.",
        "queries": [
            "product dashboard interface mockup",
            "software workflow screenshot style",
            "product planning board with digital prototype",
        ],
        "preferred_layouts": ["image_text", "table", "summary"],
        "recommended_profiles": ["product"],
    },
    "roadmap_workshops": {
        "description": "Planning-wall and roadmap-working-session imagery for timeline/strategy sequences.",
        "queries": [
            "product roadmap workshop wall",
            "milestone planning session",
            "strategy roadmap sticky notes leadership team",
        ],
        "preferred_layouts": ["timeline", "agenda", "two_column"],
        "recommended_profiles": ["product", "consulting"],
    },
    "strategy_workshops": {
        "description": "Structured offsite and strategy working-session imagery for consulting narratives.",
        "queries": [
            "executive strategy workshop offsite",
            "consulting team strategy whiteboard",
            "leadership prioritization session",
        ],
        "preferred_layouts": ["comparison", "two_column", "summary"],
        "recommended_profiles": ["consulting", "board"],
    },
    "team_alignment_sessions": {
        "description": "Alignment and planning visuals suited to change, governance, and recommendation slides.",
        "queries": [
            "leadership alignment meeting",
            "team planning session executive style",
            "stakeholder workshop executive presentation",
        ],
        "preferred_layouts": ["agenda", "faq", "summary"],
        "recommended_profiles": ["consulting", "product", "sales"],
    },
}


def list_asset_collections() -> list[str]:
    return sorted(ASSET_COLLECTIONS)


def get_asset_collection(name: str) -> dict[str, object]:
    normalized = name.strip().lower().replace("-", "_")
    if normalized not in ASSET_COLLECTIONS:
        raise ValueError(f"Unknown asset collection: {name}")
    return deepcopy(ASSET_COLLECTIONS[normalized])