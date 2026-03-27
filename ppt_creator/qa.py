from __future__ import annotations

from pathlib import Path

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput, Slide


def _issue(severity: str, message: str) -> dict[str, str]:
    return {"severity": severity, "message": message}


def _score_from_issues(issues: list[dict[str, str]]) -> int:
    penalty_map = {"high": 14, "medium": 7, "low": 3}
    score = 100
    for issue in issues:
        score -= penalty_map.get(issue["severity"], 5)
    return max(0, score)


def _review_slide(slide: Slide, *, slide_number: int, asset_missing: bool) -> dict[str, object]:
    issues: list[dict[str, str]] = []
    title = slide.title or slide.type.value

    if len(title) > 72:
        issues.append(_issue("medium", "title is long and may wrap awkwardly"))
    if slide.subtitle and len(slide.subtitle) > 120:
        issues.append(_issue("medium", "subtitle is long and may reduce visual clarity"))
    if slide.body and len(slide.body) > 260:
        issues.append(_issue("high", "body text is dense for a single executive slide"))

    if slide.bullets:
        if len(slide.bullets) > 5:
            issues.append(_issue("high", "too many bullets for executive readability"))
        long_bullets = [bullet for bullet in slide.bullets if len(bullet) > 95]
        if long_bullets:
            issues.append(_issue("medium", "one or more bullets are too long"))

    if slide.cards:
        verbose_cards = [card.title for card in slide.cards if len(card.body) > 150]
        if verbose_cards:
            issues.append(_issue("medium", f"verbose card bodies: {', '.join(verbose_cards)}"))

    if slide.metrics:
        long_metric_labels = [metric.label for metric in slide.metrics if len(metric.label) > 28]
        if long_metric_labels:
            issues.append(_issue("low", "some metric labels are long for compact KPI cards"))

    if slide.timeline_items and len(slide.timeline_items) > 4:
        issues.append(_issue("medium", "timeline may feel crowded with many steps"))

    comparison_like = slide.comparison_columns or slide.two_column_columns
    for column in comparison_like:
        if column.body and len(column.body) > 150:
            issues.append(_issue("medium", f"column '{column.title}' body may be too dense"))
        if len(column.bullets) > 3:
            issues.append(_issue("medium", f"column '{column.title}' has many bullets"))

    if slide.table_rows:
        if len(slide.table_rows) > 6:
            issues.append(_issue("high", "table has many rows and may feel overloaded"))
        if len(slide.table_columns) > 4:
            issues.append(_issue("medium", "table has many columns for executive readability"))
        any_long_cells = any(len(cell) > 38 for row in slide.table_rows for cell in row)
        if any_long_cells:
            issues.append(_issue("medium", "some table cells are likely too long"))

    if slide.faq_items:
        if len(slide.faq_items) > 3:
            issues.append(_issue("medium", "FAQ slide may feel crowded"))
        verbose_answers = [item.title for item in slide.faq_items if len(item.body) > 150]
        if verbose_answers:
            issues.append(_issue("medium", "some FAQ answers are too long"))

    if slide.chart_categories:
        if len(slide.chart_categories) > 6:
            issues.append(_issue("medium", "chart has many categories for a clean executive view"))
        if len(slide.chart_series) > 3:
            issues.append(_issue("low", "chart has many series and may become visually busy"))

    if asset_missing:
        issues.append(_issue("medium", "image asset is missing and will fall back to placeholder"))

    score = _score_from_issues(issues)
    if score >= 90:
        status = "ok"
    elif score >= 70:
        status = "review"
    else:
        status = "attention"

    return {
        "slide_number": slide_number,
        "slide_type": slide.type.value,
        "title": title,
        "score": score,
        "status": status,
        "issues": issues,
    }


def review_presentation(
    spec: PresentationInput,
    *,
    asset_root: str | Path | None = None,
    theme_name: str | None = None,
) -> dict[str, object]:
    renderer = PresentationRenderer(theme_name=theme_name or spec.presentation.theme, asset_root=asset_root)
    missing_assets = renderer.collect_missing_assets(spec)
    missing_asset_lookup = set(missing_assets)

    slides = []
    for index, slide in enumerate(spec.slides, start=1):
        title = slide.title or slide.type.value
        asset_missing = any(
            message.startswith(f"slide {index:02d} ({title})") or message.startswith(f"slide {index:02d} ({slide.type.value})")
            for message in missing_asset_lookup
        )
        slides.append(_review_slide(slide, slide_number=index, asset_missing=asset_missing))

    all_issues = [
        f"slide {slide['slide_number']:02d} ({slide['title']}): {issue['message']}"
        for slide in slides
        for issue in slide["issues"]
    ]
    average_score = int(sum(slide["score"] for slide in slides) / len(slides)) if slides else 100
    overall_status = "ok" if average_score >= 90 else "review" if average_score >= 70 else "attention"

    return {
        "mode": "review",
        "presentation_title": spec.presentation.title,
        "theme": spec.presentation.theme,
        "slide_count": len(spec.slides),
        "average_score": average_score,
        "status": overall_status,
        "issue_count": len(all_issues),
        "issues": all_issues,
        "slides": slides,
        "missing_assets": missing_assets,
    }
