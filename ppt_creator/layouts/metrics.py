from __future__ import annotations


def _metric_dense(metric, weight: float) -> bool:
    return bool(
        weight >= 2.7
        or len(metric.label) > 28
        or (metric.detail and len(metric.detail) > 78)
    )


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    components = renderer.theme.components
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "standard")
    default_eyebrow = slide_spec.eyebrow or "Key metrics"

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=default_eyebrow,
        left=g.content_left,
        top=g.title_top,
        width=7.45 if variant == "standard" else 7.15,
        subtitle_width=6.9,
    )

    metrics = slide_spec.metrics
    metric_weights = [
        renderer.estimate_content_weight(
            title=metric.label,
            body=metric.detail,
            footer=metric.trend,
            tag=metric.value,
        )
        for metric in metrics
    ]
    dense_deck = any(_metric_dense(metric, weight) for metric, weight in zip(metrics, metric_weights, strict=True))
    gap = 0.22 if dense_deck else 0.26
    left = g.content_left
    total_width = g.content_width
    top = 2.42 if variant == "standard" else 2.26
    panel_height = 2.92 if variant == "standard" else 2.30
    metric_cards = renderer.build_constrained_panel_row_content_bounds(
        left=left,
        top=top,
        width=total_width,
        height=panel_height,
        gap=gap,
        padding=0.22 if dense_deck else 0.24,
        regions=[
            {
                "kind": f"metric_{idx + 1}",
                "min_width": 1.95,
                "target_share": weight,
                "max_width": 4.35 if len(metrics) <= 3 else 3.5,
            }
            for idx, weight in enumerate(metric_weights)
        ],
    )

    for idx, (metric, weight, (panel_bounds, _)) in enumerate(zip(metrics, metric_weights, metric_cards, strict=True)):
        panel_left, panel_top, panel_width, panel_height = panel_bounds
        dense_metric = _metric_dense(metric, weight)
        value_size = (t.metric_value_size if variant == "standard" else t.metric_value_size - 4) - (2 if dense_metric else 0)
        label_size = (t.metric_label_size + 1 if variant == "standard" else t.metric_label_size) - (1 if dense_metric else 0)
        detail_size = (t.small_size + 1 if variant == "standard" else t.small_size) - (1 if dense_metric else 0)
        renderer.add_panel(
            slide,
            panel_left,
            panel_top,
            panel_width,
            panel_height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            panel_left,
            panel_top,
            panel_width,
            components.accent_bar_height,
            color=colors.navy if idx % 2 == 0 else colors.accent,
        )

        regions: list[dict[str, float | str]] = [
            {"kind": "value", "height": 0.5 if dense_metric else 0.56},
            {
                "kind": "label",
                "min_height": 0.34 if dense_metric else 0.30,
                "max_height": 0.56,
                "target_share": renderer.estimate_content_weight(title=metric.label),
            },
        ]
        if metric.detail:
            regions.append(
                {
                    "kind": "detail",
                    "min_height": 0.34 if dense_metric else 0.28,
                    "target_share": renderer.estimate_content_weight(body=metric.detail),
                }
            )
        if metric.trend:
            regions.append({"kind": "trend", "height": 0.30})

        for region, (region_left, region_top, region_width, region_height) in renderer.build_constrained_panel_content_stack_bounds(
            left=panel_left,
            top=panel_top,
            width=panel_width,
            height=panel_height,
            regions=regions,
            gap=0.06 if dense_metric else 0.08,
            padding=0.22 if dense_metric else 0.24,
        ):
            box = renderer.textbox(slide, region_left, region_top, region_width, region_height)
            if region["kind"] == "value":
                renderer.write_paragraph(box.text_frame, metric.value, size=value_size, color=colors.navy, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=value_size, min_size=t.metric_label_size + 4, bold=True)
            elif region["kind"] == "label":
                renderer.write_paragraph(box.text_frame, metric.label, size=label_size, color=colors.text, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=label_size, min_size=t.small_size + 1, bold=True)
            elif region["kind"] == "detail":
                renderer.write_paragraph(box.text_frame, metric.detail or "", size=detail_size, color=colors.muted)
                renderer.fit_text_frame(box.text_frame, max_size=detail_size, min_size=t.small_size - 1)
            else:
                renderer.write_paragraph(box.text_frame, metric.trend or "", size=detail_size, color=colors.accent, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=detail_size, min_size=t.small_size - 1, bold=True)
