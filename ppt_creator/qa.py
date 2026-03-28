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


def _estimate_text_mass(
    *,
    title: str | None = None,
    body: str | None = None,
    bullets: list[str] | None = None,
    footer: str | None = None,
    tag: str | None = None,
) -> float:
    bullet_items = bullets or []
    mass = 0.0
    if title:
        mass += len(title.split()) * 0.7
    if body:
        mass += len(body.split()) * 1.0
    if footer:
        mass += len(footer.split()) * 0.45
    if tag:
        mass += len(tag.split()) * 0.3
    for bullet in bullet_items:
        mass += len(bullet.split()) * 1.1
    return round(mass, 2)


def _region_density(
    *,
    width: float,
    height: float,
    title: str | None = None,
    body: str | None = None,
    bullets: list[str] | None = None,
    footer: str | None = None,
    tag: str | None = None,
) -> float:
    area = max(0.35, width * height)
    return round(
        _estimate_text_mass(title=title, body=body, bullets=bullets, footer=footer, tag=tag) / area,
        3,
    )


def _build_layout_pressure_signals(renderer: PresentationRenderer, slide: Slide) -> list[dict[str, object]]:
    g = renderer.theme.grid
    signals: list[dict[str, object]] = []

    def add_signal(*, region: str, density: float, threshold: float, message: str) -> None:
        if density < threshold:
            return
        signals.append(
            {
                "region": region,
                "density": density,
                "threshold": threshold,
                "severity": "high" if density >= threshold * 1.3 else "medium",
                "message": message,
            }
        )

    if slide.type.value == "agenda":
        bullet_weights = [renderer.estimate_content_weight(body=bullet) for bullet in slide.bullets]
        stack_regions: list[dict[str, float | str]] = []
        if slide.body:
            stack_regions.append(
                {
                    "kind": "intro",
                    "min_height": 0.56,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(body=slide.body),
                }
            )
        stack_regions.append(
            {
                "kind": "agenda_rows",
                "min_height": 2.6,
                "flex": 1.0,
                "content_weight": sum(bullet_weights) or 1.0,
            }
        )
        content_stack = renderer.build_content_stack(
            top=2.2,
            height=3.9,
            regions=stack_regions,
            gap=0.18,
            min_flex=0.9,
            max_flex=1.25,
        )
        for region, (_, region_height) in content_stack:
            if region["kind"] == "intro" and slide.body:
                density = _region_density(width=g.content_width, height=region_height, body=slide.body)
                add_signal(
                    region="agenda:intro",
                    density=density,
                    threshold=4.1,
                    message="agenda intro region is dense enough to risk vertical crowding",
                )
            elif region["kind"] == "agenda_rows" and slide.bullets:
                row_bounds = renderer.build_weighted_rows(
                    top=0.0,
                    height=region_height,
                    gap=0.16,
                    weights=bullet_weights,
                    min_height=0.46,
                    min_flex=0.9,
                    max_flex=1.2,
                    kind_prefix="agenda_row",
                )
                for index, (bullet, (_, row_height)) in enumerate(zip(slide.bullets, row_bounds, strict=True), start=1):
                    density = _region_density(
                        width=g.content_width - 0.95,
                        height=max(0.28, row_height - 0.18),
                        body=bullet,
                    )
                    add_signal(
                        region=f"agenda:row_{index}",
                        density=density,
                        threshold=3.8,
                        message=f"agenda row {index} is tightly packed and may collide vertically",
                    )

    elif slide.type.value == "bullets":
        variant = renderer.resolve_layout_variant(slide, "insight_panel")
        if variant == "insight_panel":
            split_weights = [
                renderer.estimate_content_weight(title=slide.title, body=slide.body, bullets=slide.bullets),
                renderer.estimate_content_weight(
                    title="Executive lens",
                    body="Keep decision-making crisp, reduce operational drag, and let human sellers spend more time in high-value conversations.",
                    bullets=["clarity", "consistency", "measurable lift"],
                ),
            ]
            split_columns = renderer.build_weighted_columns(
                left=g.content_left,
                width=g.content_width,
                gap=0.35,
                weights=split_weights,
                min_width=3.4,
                min_flex=0.9,
                max_flex=1.3,
                kind_prefix="bullets_split",
            )
            _, left_width = split_columns[0]
        else:
            left_width = g.content_width

        text_regions: list[dict[str, float | str]] = []
        if slide.body:
            if slide.bullets:
                text_regions.append(
                    {
                        "kind": "body",
                        "min_height": 0.92,
                        "flex": 1.0,
                        "content_weight": renderer.estimate_content_weight(body=slide.body),
                    }
                )
            else:
                text_regions.append({"kind": "body", "height": 3.15})
        if slide.bullets:
            text_regions.append(
                {
                    "kind": "bullets",
                    "min_height": 1.45 if slide.body else 3.15,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(bullets=slide.bullets),
                }
            )
        for region, (_, region_height) in renderer.build_content_stack(
            top=2.55,
            height=3.15,
            regions=text_regions,
            gap=0.18,
            min_flex=0.9,
            max_flex=1.35,
        ):
            if region["kind"] == "body" and slide.body:
                density = _region_density(width=left_width, height=region_height, body=slide.body)
                add_signal(
                    region="bullets:body",
                    density=density,
                    threshold=4.1,
                    message="bullets narrative region is dense enough to risk text collisions",
                )
            elif region["kind"] == "bullets" and slide.bullets:
                density = _region_density(width=left_width, height=region_height, bullets=slide.bullets)
                add_signal(
                    region="bullets:list",
                    density=density,
                    threshold=3.9,
                    message="bullet list region is dense enough to risk crowding or overlap",
                )

    elif slide.type.value == "summary":
        has_body = bool(slide.body)
        has_bullets = bool(slide.bullets)
        if has_body and has_bullets:
            split_flexes = renderer.normalize_content_flexes(
                [
                    renderer.estimate_content_weight(title=slide.title, body=slide.body),
                    renderer.estimate_content_weight(bullets=slide.bullets),
                ],
                min_flex=0.9,
                max_flex=1.4,
            )
            split_regions = renderer.build_columns(
                left=g.content_left,
                width=g.content_width,
                regions=[
                    {"kind": "narrative", "min_width": 6.2, "flex": split_flexes[0]},
                    {"kind": "panel", "min_width": 3.4, "flex": split_flexes[1]},
                ],
                gap=0.35,
            )
            _, narrative_width = split_regions[0]
            panel_left, panel_width = split_regions[1]
            density = _region_density(width=narrative_width, height=1.55, body=slide.body)
            add_signal(
                region="summary:narrative",
                density=density,
                threshold=4.2,
                message="summary narrative region is dense enough to risk crowding",
            )

            content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
                left=panel_left,
                top=2.1,
                width=panel_width,
                height=3.2,
                padding=0.26,
            )
            panel_regions = renderer.stack_vertical_regions(
                top=content_top,
                height=content_height,
                regions=[
                    {"kind": "heading", "height": 0.28},
                    {"kind": "bullets", "min_height": 2.18, "flex": 1.0},
                ],
                gap=0.08,
            )
            bullet_height = panel_regions[1][1][1]
            density = _region_density(width=content_width, height=bullet_height, bullets=slide.bullets)
            add_signal(
                region="summary:takeaways",
                density=density,
                threshold=3.8,
                message="summary takeaways panel is dense enough to risk clipping",
            )
        elif has_body:
            density = _region_density(width=g.content_width, height=1.9, body=slide.body)
            add_signal(
                region="summary:body",
                density=density,
                threshold=4.4,
                message="summary body region is dense enough to risk crowding",
            )
        elif has_bullets:
            density = _region_density(width=g.content_width - 0.56, height=1.9, bullets=slide.bullets)
            add_signal(
                region="summary:bullets",
                density=density,
                threshold=3.9,
                message="summary bullet panel is dense enough to risk crowding",
            )

    elif slide.type.value in {"comparison", "two_column"}:
        columns = slide.comparison_columns or slide.two_column_columns
        weights = [
            renderer.estimate_content_weight(
                title=column.title,
                body=column.body,
                bullets=column.bullets,
                footer=column.footer,
                tag=column.tag,
            )
            for column in columns
        ]
        panel_bounds = renderer.build_panel_row_bounds(
            left=g.content_left,
            top=2.45,
            width=g.content_width,
            height=3.25,
            gap=0.42,
            min_width=3.6,
            regions=[
                {"kind": f"comparison_{index + 1}", "min_width": 3.6, "flex": flex}
                for index, flex in enumerate(
                    renderer.normalize_content_flexes(weights, min_flex=0.95, max_flex=1.2)
                )
            ],
        )
        for index, (column, (left, panel_top, panel_width, panel_height)) in enumerate(zip(columns, panel_bounds, strict=True), start=1):
            content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
                left=left,
                top=panel_top,
                width=panel_width,
                height=panel_height,
                padding=0.28,
            )
            total_density = _region_density(
                width=content_width,
                height=content_height,
                title=column.title,
                body=column.body,
                bullets=column.bullets,
                footer=column.footer,
                tag=column.tag,
            )
            add_signal(
                region=f"comparison:column_{index}",
                density=total_density,
                threshold=3.7,
                message=f"column '{column.title}' is dense enough to risk internal collisions",
            )

    elif slide.type.value == "table" and slide.table_rows and slide.table_columns:
        column_flexes = renderer.normalize_content_flexes(
            [
                renderer.estimate_content_weight(
                    title=column,
                    body=" ".join(row[index] for row in slide.table_rows if index < len(row)),
                )
                for index, column in enumerate(slide.table_columns)
            ],
            min_flex=0.85,
            max_flex=1.5,
        )
        column_bounds = renderer.build_columns(
            left=g.content_left,
            width=g.content_width,
            gap=0.06,
            min_width=1.0,
            regions=[
                {"kind": f"column_{index + 1}", "min_width": 1.0, "flex": flex}
                for index, flex in enumerate(column_flexes)
            ],
        )
        for row_index, row in enumerate(slide.table_rows, start=1):
            for col_index, (cell, (_, column_width)) in enumerate(zip(row, column_bounds, strict=True), start=1):
                density = _region_density(width=max(0.4, column_width - 0.12), height=0.32, body=cell)
                add_signal(
                    region=f"table:r{row_index}c{col_index}",
                    density=density,
                    threshold=8.0,
                    message=f"table cell r{row_index}c{col_index} is dense enough to risk clipping",
                )

    return signals


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


def _risk_score(slide_review: dict[str, object]) -> float:
    severity_counts = slide_review["severity_counts"]
    return (
        float(slide_review["overflow_risk_count"]) * 2.0
        + float(slide_review["collision_risk_count"]) * 1.7
        + float(slide_review["balance_warning_count"]) * 1.2
        + float(slide_review["layout_pressure_score"]) * 0.45
        + float(severity_counts["high"]) * 2.5
        + float(severity_counts["medium"]) * 1.4
        + float(severity_counts["low"]) * 0.6
    )


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
    clipping_risk_count = 0
    collision_risk_count = 0
    balance_warning_count = 0
    content_weight = _slide_content_weight(renderer, slide)
    likely_overflow_regions: list[str] = []
    likely_collision_regions: list[str] = []

    if len(title) > 72:
        issues.append(_issue("medium", "title is long and may wrap awkwardly"))
    if slide.subtitle and len(slide.subtitle) > 120:
        issues.append(_issue("medium", "subtitle is long and may reduce visual clarity"))
    if slide.body and len(slide.body) > 260:
        issues.append(_issue("high", "body text is dense for a single executive slide"))
        clipping_risk_count += 1
        likely_overflow_regions.append("body")

    if slide.bullets:
        if len(slide.bullets) > 5:
            issues.append(_issue("high", "too many bullets for executive readability"))
            clipping_risk_count += 1
            likely_overflow_regions.append("bullets")
        long_bullets = [bullet for bullet in slide.bullets if len(bullet) > 95]
        if long_bullets:
            issues.append(_issue("medium", "one or more bullets are too long"))
            clipping_risk_count += 1
            likely_overflow_regions.append("bullets")

    if slide.cards:
        verbose_cards = [card.title for card in slide.cards if len(card.body) > 150]
        if verbose_cards:
            issues.append(_issue("medium", f"verbose card bodies: {', '.join(verbose_cards)}"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append("cards")
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
            clipping_risk_count += 1
            likely_overflow_regions.append("metrics")
        if _balance_ratio(metric_weights) >= 1.45:
            issues.append(_issue("low", "metric cards may feel visually uneven"))
            balance_warning_count += 1

    if slide.timeline_items and len(slide.timeline_items) > 4:
        issues.append(_issue("medium", "timeline may feel crowded with many steps"))
        overflow_risk_count += 1
        clipping_risk_count += 1
        likely_overflow_regions.append("timeline")

    comparison_like = slide.comparison_columns or slide.two_column_columns
    comparison_weights: list[float] = []
    for column in comparison_like:
        if column.body and len(column.body) > 150:
            issues.append(_issue("medium", f"column '{column.title}' body may be too dense"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append(f"column:{column.title}:body")
        if len(column.bullets) > 3:
            issues.append(_issue("medium", f"column '{column.title}' has many bullets"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append(f"column:{column.title}:bullets")
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
            clipping_risk_count += 1
            likely_overflow_regions.append("table")
        if len(slide.table_columns) > 4:
            issues.append(_issue("medium", "table has many columns for executive readability"))
        any_long_cells = any(len(cell) > 38 for row in slide.table_rows for cell in row)
        if any_long_cells:
            issues.append(_issue("medium", "some table cells are likely too long"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append("table")
        row_weights = [renderer.estimate_content_weight(body=" ".join(row)) for row in slide.table_rows]
        if _balance_ratio(row_weights) >= 1.75:
            issues.append(_issue("low", "table rows vary significantly in density and may look uneven"))
            balance_warning_count += 1

    if slide.faq_items:
        if len(slide.faq_items) > 3:
            issues.append(_issue("medium", "FAQ slide may feel crowded"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append("faq")
        verbose_answers = [item.title for item in slide.faq_items if len(item.body) > 150]
        if verbose_answers:
            issues.append(_issue("medium", "some FAQ answers are too long"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append("faq")
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
            clipping_risk_count += 1
            likely_overflow_regions.append("mixed_text")

    if slide.type.value == "agenda":
        bullet_weights = [renderer.estimate_content_weight(body=bullet) for bullet in slide.bullets]
        if bullet_weights and max(bullet_weights) > 2.1:
            issues.append(_issue("medium", "one or more agenda rows are too verbose"))
            overflow_risk_count += 1
            clipping_risk_count += 1
            likely_overflow_regions.append("agenda_rows")

    if slide.type.value == "closing" and len((slide.quote or slide.body or "")) > 220:
        issues.append(_issue("medium", "closing quote is long and may reduce visual impact"))
        overflow_risk_count += 1
        clipping_risk_count += 1
        likely_overflow_regions.append("closing_quote")

    if asset_missing:
        issues.append(_issue("medium", "image asset is missing and will fall back to placeholder"))

    layout_pressure_signals = _build_layout_pressure_signals(renderer, slide)
    layout_pressure_score = round(
        sum(float(signal["density"]) - float(signal["threshold"]) for signal in layout_pressure_signals),
        2,
    )
    for signal in layout_pressure_signals:
        issues.append(_issue(str(signal["severity"]), str(signal["message"])))
        collision_risk_count += 1
        likely_collision_regions.append(str(signal["region"]))

    score = _score_from_issues(issues)
    if score >= 90:
        status = "ok"
    elif score >= 70:
        status = "review"
    else:
        status = "attention"

    risk_level = "low"
    if clipping_risk_count >= 2 or collision_risk_count >= 2 or _severity_counts(issues)["high"]:
        risk_level = "high"
    elif overflow_risk_count or collision_risk_count or balance_warning_count:
        risk_level = "medium"

    return {
        "slide_number": slide_number,
        "slide_type": slide.type.value,
        "title": title,
        "score": score,
        "status": status,
        "content_weight": content_weight,
        "overflow_risk_count": overflow_risk_count,
        "clipping_risk_count": clipping_risk_count,
        "collision_risk_count": collision_risk_count,
        "balance_warning_count": balance_warning_count,
        "layout_pressure_score": layout_pressure_score,
        "risk_level": risk_level,
        "likely_overflow_regions": sorted(set(likely_overflow_regions)),
        "likely_collision_regions": sorted(set(likely_collision_regions)),
        "layout_pressure_signals": layout_pressure_signals,
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
    clipping_risk_count = sum(int(slide["clipping_risk_count"]) for slide in slides)
    collision_risk_count = sum(int(slide["collision_risk_count"]) for slide in slides)
    balance_warning_count = sum(int(slide["balance_warning_count"]) for slide in slides)
    top_risk_slides = [
        {
            "slide_number": slide["slide_number"],
            "title": slide["title"],
            "risk_level": slide["risk_level"],
            "overflow_risk_count": slide["overflow_risk_count"],
            "clipping_risk_count": slide["clipping_risk_count"],
            "collision_risk_count": slide["collision_risk_count"],
            "balance_warning_count": slide["balance_warning_count"],
            "layout_pressure_score": slide["layout_pressure_score"],
        }
        for slide in sorted(slides, key=_risk_score, reverse=True)[:5]
        if _risk_score(slide) > 0
    ]

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
        "clipping_risk_count": clipping_risk_count,
        "collision_risk_count": collision_risk_count,
        "balance_warning_count": balance_warning_count,
        "top_risk_slides": top_risk_slides,
        "issues": all_issues,
        "warnings": all_issues,
        "slides": slides,
        "missing_assets": missing_assets,
    }
