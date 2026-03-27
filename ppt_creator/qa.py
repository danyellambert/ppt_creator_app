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


def _severity_counts(issues: list[dict[str, str]]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        severity = issue.get("severity", "low")
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _balance_ratio(weights: list[float]) -> float:
    positive = [weight for weight in weights if weight > 0]
    if len(positive) < 2:
        return 1.0
    low = min(positive)
    high = max(positive)
    return high / low if low else high


def _slide_content_weight(renderer: PresentationRenderer, slide: Slide) -> float:
    weight = renderer.estimate_content_weight(
        title=slide.title,
        body=slide.body,
        bullets=slide.bullets,
        footer=slide.attribution or slide.image_caption,
        tag=slide.eyebrow or slide.section_label,
    )
    weight += sum(
        renderer.estimate_content_weight(title=card.title, body=card.body, footer=card.footer)
        for card in slide.cards
    )
    weight += sum(
        renderer.estimate_content_weight(title=metric.label, body=metric.detail, footer=metric.trend)
        for metric in slide.metrics
    )
    weight += sum(
        renderer.estimate_content_weight(title=item.title, body=item.body, footer=item.footer, tag=item.tag)
        for item in slide.timeline_items
    )
    weight += sum(
        renderer.estimate_content_weight(
            title=column.title,
            body=column.body,
            bullets=column.bullets,
            footer=column.footer,
            tag=column.tag,
        )
        for column in slide.comparison_columns + slide.two_column_columns
    )
    weight += sum(
        renderer.estimate_content_weight(title=item.title, body=item.body)
        for item in slide.faq_items
    )
    if slide.table_rows:
        weight += sum(renderer.estimate_content_weight(body=" ".join(row)) for row in slide.table_rows)
    if slide.chart_categories:
        weight += renderer.estimate_content_weight(body=" ".join(slide.chart_categories))
    return round(weight, 2)


def _review_slide(
    slide: Slide,
    *,
    slide_number: int,
    asset_missing: bool,
    renderer: PresentationRenderer,
) -> dict[str, object]:
    issues: list[dict[str, str]] = []
    title = slide.title or slide.type.value
    overflow_risk_count = 0
    balance_warning_count = 0
    content_weight = _slide_content_weight(renderer, slide)

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
            overflow_risk_count += 1
        card_weights = [
            renderer.estimate_content_weight(title=card.title, body=card.body, footer=card.footer)
            for card in slide.cards
        ]
        if _balance_ratio(card_weights) >= 1.55:
            issues.append(_issue("low", "card content looks uneven and may create visual imbalance"))
            balance_warning_count += 1

    if slide.metrics:
        long_metric_labels = [metric.label for metric in slide.metrics if len(metric.label) > 28]
        if long_metric_labels:
            issues.append(_issue("low", "some metric labels are long for compact KPI cards"))
        metric_weights = [
            renderer.estimate_content_weight(title=metric.label, body=metric.detail, footer=metric.trend)
            for metric in slide.metrics
        ]
        if metric_weights and max(metric_weights) > 3.0:
            issues.append(_issue("medium", "one or more metric cards may feel too dense"))
            overflow_risk_count += 1
        if _balance_ratio(metric_weights) >= 1.45:
            issues.append(_issue("low", "metric cards may feel visually uneven"))
            balance_warning_count += 1

    if slide.timeline_items and len(slide.timeline_items) > 4:
        issues.append(_issue("medium", "timeline may feel crowded with many steps"))
        overflow_risk_count += 1

    comparison_like = slide.comparison_columns or slide.two_column_columns
    comparison_weights: list[float] = []
    for column in comparison_like:
        if column.body and len(column.body) > 150:
            issues.append(_issue("medium", f"column '{column.title}' body may be too dense"))
            overflow_risk_count += 1
        if len(column.bullets) > 3:
            issues.append(_issue("medium", f"column '{column.title}' has many bullets"))
            overflow_risk_count += 1
        comparison_weights.append(
            renderer.estimate_content_weight(
                title=column.title,
                body=column.body,
                bullets=column.bullets,
                footer=column.footer,
                tag=column.tag,
            )
        )

    if comparison_weights and _balance_ratio(comparison_weights) >= 1.65:
        issues.append(_issue("medium", "comparison-like columns are imbalanced and may compete for space"))
        balance_warning_count += 1

    if slide.table_rows:
        if len(slide.table_rows) > 6:
            issues.append(_issue("high", "table has many rows and may feel overloaded"))
            overflow_risk_count += 1
        if len(slide.table_columns) > 4:
            issues.append(_issue("medium", "table has many columns for executive readability"))
        any_long_cells = any(len(cell) > 38 for row in slide.table_rows for cell in row)
        if any_long_cells:
            issues.append(_issue("medium", "some table cells are likely too long"))
            overflow_risk_count += 1
        row_weights = [renderer.estimate_content_weight(body=" ".join(row)) for row in slide.table_rows]
        if _balance_ratio(row_weights) >= 1.75:
            issues.append(_issue("low", "table rows vary significantly in density and may look uneven"))
            balance_warning_count += 1

    if slide.faq_items:
        if len(slide.faq_items) > 3:
            issues.append(_issue("medium", "FAQ slide may feel crowded"))
            overflow_risk_count += 1
        verbose_answers = [item.title for item in slide.faq_items if len(item.body) > 150]
        if verbose_answers:
            issues.append(_issue("medium", "some FAQ answers are too long"))
            overflow_risk_count += 1
        faq_weights = [renderer.estimate_content_weight(title=item.title, body=item.body) for item in slide.faq_items]
        if _balance_ratio(faq_weights) >= 1.7:
            issues.append(_issue("low", "FAQ items are imbalanced and may produce uneven panels"))
            balance_warning_count += 1

    if slide.chart_categories:
        if len(slide.chart_categories) > 6:
            issues.append(_issue("medium", "chart has many categories for a clean executive view"))
        if len(slide.chart_series) > 3:
            issues.append(_issue("low", "chart has many series and may become visually busy"))

    if slide.type.value in {"agenda", "bullets", "image_text", "summary"} and slide.body and slide.bullets:
        mixed_weights = [
            renderer.estimate_content_weight(body=slide.body),
            renderer.estimate_content_weight(bullets=slide.bullets),
        ]
        if _balance_ratio(mixed_weights) >= 1.8:
            issues.append(_issue("low", "body and bullet regions are imbalanced and may compete for vertical space"))
            balance_warning_count += 1
        if sum(mixed_weights) >= 5.4:
            issues.append(_issue("medium", "mixed narrative content is dense and may overflow vertically"))
            overflow_risk_count += 1

    if slide.type.value == "agenda":
        bullet_weights = [renderer.estimate_content_weight(body=bullet) for bullet in slide.bullets]
        if bullet_weights and max(bullet_weights) > 2.1:
            issues.append(_issue("medium", "one or more agenda rows are too verbose"))
            overflow_risk_count += 1

    if slide.type.value == "closing" and len((slide.quote or slide.body or "")) > 220:
        issues.append(_issue("medium", "closing quote is long and may reduce visual impact"))
        overflow_risk_count += 1

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
        "content_weight": content_weight,
        "overflow_risk_count": overflow_risk_count,
        "balance_warning_count": balance_warning_count,
        "severity_counts": _severity_counts(issues),
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
        slides.append(
            _review_slide(
                slide,
                slide_number=index,
                asset_missing=asset_missing,
                renderer=renderer,
            )
        )

    all_issues = [
        f"slide {slide['slide_number']:02d} ({slide['title']}): {issue['message']}"
        for slide in slides
        for issue in slide["issues"]
    ]
    average_score = int(sum(slide["score"] for slide in slides) / len(slides)) if slides else 100
    overall_status = "ok" if average_score >= 90 else "review" if average_score >= 70 else "attention"
    severity_counts = {
        "high": sum(int(slide["severity_counts"]["high"]) for slide in slides),
        "medium": sum(int(slide["severity_counts"]["medium"]) for slide in slides),
        "low": sum(int(slide["severity_counts"]["low"]) for slide in slides),
    }
    overflow_risk_count = sum(int(slide["overflow_risk_count"]) for slide in slides)
    balance_warning_count = sum(int(slide["balance_warning_count"]) for slide in slides)

    return {
        "mode": "review",
        "presentation_title": spec.presentation.title,
        "theme": spec.presentation.theme,
        "slide_count": len(spec.slides),
        "average_score": average_score,
        "status": overall_status,
        "issue_count": len(all_issues),
        "warning_count": len(all_issues),
        "severity_counts": severity_counts,
        "overflow_risk_count": overflow_risk_count,
        "balance_warning_count": balance_warning_count,
        "issues": all_issues,
        "warnings": all_issues,
        "slides": slides,
        "missing_assets": missing_assets,
    }
