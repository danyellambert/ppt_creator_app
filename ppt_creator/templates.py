from __future__ import annotations

import json

DOMAIN_TEMPLATES: dict[str, dict[str, object]] = {
    "sales": {
        "presentation": {
            "title": "Sales operating review",
            "subtitle": "Commercial performance and execution priorities",
            "client_name": "Revenue Leadership",
            "author": "PPT Creator",
            "date": "2026-03-26",
            "theme": "dark_boardroom",
            "footer_text": "Sales template",
        },
        "slides": [
            {
                "type": "title",
                "title": "Sales operating review",
                "subtitle": "Commercial performance and execution priorities",
                "layout_variant": "hero_cover",
                "eyebrow": "Sales template",
            },
            {
                "type": "agenda",
                "title": "Agenda",
                "bullets": ["Performance", "Pipeline", "Execution risks", "Next actions"],
            },
            {
                "type": "metrics",
                "title": "Headline performance",
                "metrics": [
                    {"value": "$8.4M", "label": "pipeline added"},
                    {"value": "31%", "label": "win rate"},
                    {"value": "104%", "label": "plan attainment"},
                ],
            },
            {
                "type": "summary",
                "title": "Executive summary",
                "bullets": [
                    "Protect pipeline quality",
                    "Reduce deal slippage",
                    "Focus coaching on conversion moments",
                ],
            },
            {"type": "closing", "title": "Closing thought", "quote": "Execution quality compounds when the operating rhythm stays consistent."},
        ],
    },
    "consulting": {
        "presentation": {
            "title": "Consulting engagement review",
            "subtitle": "Client situation, options, and recommendation",
            "client_name": "Client Name",
            "author": "PPT Creator",
            "date": "2026-03-26",
            "theme": "consulting_clean",
            "footer_text": "Consulting template",
        },
        "slides": [
            {
                "type": "title",
                "title": "Consulting engagement review",
                "subtitle": "Client situation, options, and recommendation",
                "layout_variant": "hero_cover",
                "eyebrow": "Consulting template",
            },
            {
                "type": "agenda",
                "title": "Discussion flow",
                "bullets": ["Situation", "Diagnosis", "Options", "Recommendation"],
            },
            {
                "type": "comparison",
                "title": "Option framing",
                "comparison_columns": [
                    {"title": "Current approach", "body": "The organization keeps absorbing unnecessary complexity."},
                    {"title": "Recommended approach", "bullets": ["Simplify priorities", "Clarify ownership", "Sequence execution"]},
                ],
            },
            {
                "type": "summary",
                "title": "Recommendation",
                "body": "The recommended path reduces complexity first, then scales only after decision clarity improves.",
                "bullets": ["Narrow scope", "Clarify decisions", "Measure progress monthly"],
            },
            {"type": "closing", "title": "Closing thought", "quote": "A stronger operating model is usually the result of fewer, clearer choices."},
        ],
    },
    "strategy": {
        "presentation": {
            "title": "Strategy review",
            "subtitle": "Priorities, trade-offs, and sequencing",
            "client_name": "Strategy Office",
            "author": "PPT Creator",
            "date": "2026-03-26",
            "theme": "executive_premium_minimal",
            "footer_text": "Strategy template",
        },
        "slides": [
            {
                "type": "title",
                "title": "Strategy review",
                "subtitle": "Priorities, trade-offs, and sequencing",
                "layout_variant": "hero_cover",
                "eyebrow": "Strategy template",
            },
            {
                "type": "timeline",
                "title": "Strategic sequence",
                "timeline_items": [
                    {"title": "Diagnose", "body": "Clarify the few questions that matter most."},
                    {"title": "Decide", "body": "Choose the winning priorities and explicit trade-offs."},
                    {"title": "Sequence", "body": "Stage execution in a realistic order."},
                ],
            },
            {
                "type": "two_column",
                "title": "Strategic trade-off",
                "two_column_columns": [
                    {"title": "If focus drifts", "body": "Execution spreads too thin and decisions stay noisy."},
                    {"title": "If focus sharpens", "bullets": ["Clearer trade-offs", "Better capital allocation", "Faster learning"]},
                ],
            },
            {
                "type": "summary",
                "title": "Executive summary",
                "bullets": ["Focus on fewer bets", "Stage execution deliberately", "Review strategy through measurable milestones"],
            },
            {"type": "closing", "title": "Closing thought", "quote": "Strategy compounds when sequencing is as disciplined as ambition."},
        ],
    },
    "product": {
        "presentation": {
            "title": "Product portfolio review",
            "subtitle": "Roadmap, adoption, and product decisions",
            "client_name": "Product Leadership",
            "author": "PPT Creator",
            "date": "2026-03-26",
            "theme": "startup_minimal",
            "footer_text": "Product template",
        },
        "slides": [
            {
                "type": "title",
                "title": "Product portfolio review",
                "subtitle": "Roadmap, adoption, and product decisions",
                "layout_variant": "hero_cover",
                "eyebrow": "Product template",
            },
            {
                "type": "agenda",
                "title": "Agenda",
                "bullets": ["Product signals", "Roadmap choices", "Risks", "Next quarter"],
            },
            {
                "type": "table",
                "title": "Portfolio snapshot",
                "table_columns": ["Area", "Status", "Action"],
                "table_rows": [
                    ["Core workflow", "Healthy", "Sustain investment"],
                    ["New bets", "Mixed", "Reduce parallel scope"],
                ],
            },
            {
                "type": "faq",
                "title": "Leadership FAQ",
                "faq_items": [
                    {"title": "What should move first?", "body": "Prioritize the workflow with the strongest usage pull and clearest value signal."},
                    {"title": "What should wait?", "body": "Pause low-conviction initiatives until the roadmap is more concentrated."},
                ],
            },
            {
                "type": "summary",
                "title": "Recommendation",
                "bullets": ["Concentrate roadmap scope", "Protect core adoption", "Use clear decision gates"],
            },
        ],
    },
}


def list_template_domains() -> list[str]:
    return sorted(DOMAIN_TEMPLATES)


def build_domain_template(domain: str, *, theme_name: str | None = None) -> dict[str, object]:
    normalized = domain.strip().lower().replace("-", "_")
    if normalized not in DOMAIN_TEMPLATES:
        raise ValueError(f"Unknown template domain: {domain}")

    payload = json.loads(json.dumps(DOMAIN_TEMPLATES[normalized]))
    if theme_name:
        payload["presentation"]["theme"] = theme_name
    return payload
