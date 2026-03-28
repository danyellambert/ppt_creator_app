from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    g = renderer.theme.grid
    t = renderer.theme.typography
    components = renderer.theme.components
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "standard")

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 5.2, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)
        renderer.fit_text_frame(eyebrow_box.text_frame, max_size=t.eyebrow_size, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 6.8, 0.8)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)
    renderer.fit_text_frame(title_box.text_frame, max_size=t.title_size, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.8, 7.0, 0.4)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)
        renderer.fit_text_frame(subtitle_box.text_frame, max_size=t.subtitle_size)

    metrics = slide_spec.metrics
    gap = 0.28
    left = g.content_left
    total_width = g.content_width
    top = 2.55 if variant == "standard" else 2.35
    panel_height = 2.7 if variant == "standard" else 2.15
    value_size = t.metric_value_size if variant == "standard" else t.metric_value_size - 4
    label_size = t.metric_label_size + 1 if variant == "standard" else t.metric_label_size
    detail_size = t.small_size + 1 if variant == "standard" else t.small_size
    metric_flexes = renderer.normalize_content_flexes(
        [
            renderer.estimate_content_weight(
                title=metric.label,
                body=metric.detail,
                footer=metric.trend,
            )
            for metric in metrics
        ],
        min_flex=0.95,
        max_flex=1.25,
    )

    metric_cards = renderer.build_weighted_panel_row_content_bounds(
        left=left,
        top=top,
        width=total_width,
        height=panel_height,
        gap=gap,
        weights=metric_flexes,
        min_width=1.8,
        padding=0.24,
        kind_prefix="metric",
        min_flex=0.95,
        max_flex=1.25,
    )

    for idx, (metric, (panel_bounds, content_bounds)) in enumerate(zip(metrics, metric_cards, strict=True)):
        panel_left, panel_top, panel_width, panel_height = panel_bounds
        content_left, content_top, content_width, content_height = content_bounds
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
            {"kind": "value", "height": 0.52},
            {"kind": "label", "height": 0.34},
        ]
        if metric.detail:
            regions.append(
                {
                    "kind": "detail",
                    "min_height": 0.28,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(body=metric.detail),
                }
            )
        if metric.trend:
            regions.append({"kind": "trend", "height": 0.30})

        for region, (region_top, region_height) in renderer.build_content_stack(
            top=content_top + 0.06,
            height=max(0.4, content_height - 0.06),
            regions=regions,
            gap=0.08,
            min_flex=0.9,
            max_flex=1.35,
        ):
            box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
            if region["kind"] == "value":
                renderer.write_paragraph(box.text_frame, metric.value, size=value_size, color=colors.navy, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=value_size, bold=True)
            elif region["kind"] == "label":
                renderer.write_paragraph(box.text_frame, metric.label, size=label_size, color=colors.text, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=label_size, bold=True)
            elif region["kind"] == "detail":
                renderer.write_paragraph(box.text_frame, metric.detail or "", size=detail_size, color=colors.muted)
                renderer.fit_text_frame(box.text_frame, max_size=detail_size)
            else:
                renderer.write_paragraph(box.text_frame, metric.trend or "", size=detail_size, color=colors.accent, bold=True)
                renderer.fit_text_frame(box.text_frame, max_size=detail_size, bold=True)
