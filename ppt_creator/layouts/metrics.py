from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
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
    count = len(metrics)
    gap = 0.28
    total_width = 11.63
    card_width = (total_width - gap * (count - 1)) / count
    left = c.margin_x
    top = 2.55 if variant == "standard" else 2.35
    panel_height = 2.7 if variant == "standard" else 2.15
    value_size = t.metric_value_size if variant == "standard" else t.metric_value_size - 4
    label_size = t.metric_label_size + 1 if variant == "standard" else t.metric_label_size
    detail_size = t.small_size + 1 if variant == "standard" else t.small_size

    for idx, metric in enumerate(metrics):
        x = left + idx * (card_width + gap)
        renderer.add_panel(slide, x, top, card_width, panel_height, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, x, top, card_width, components.accent_bar_height, color=colors.navy if idx % 2 == 0 else colors.accent)

        inner_left = x + 0.24
        inner_width = card_width - 0.48

        value_box = renderer.textbox(slide, inner_left, top + 0.30, inner_width, 0.52)
        renderer.write_paragraph(value_box.text_frame, metric.value, size=value_size, color=colors.navy, bold=True)
        renderer.fit_text_frame(value_box.text_frame, max_size=value_size, bold=True)

        label_box = renderer.textbox(slide, inner_left, top + 0.92, inner_width, 0.34)
        renderer.write_paragraph(label_box.text_frame, metric.label, size=label_size, color=colors.text, bold=True)
        renderer.fit_text_frame(label_box.text_frame, max_size=label_size, bold=True)

        details_top = top + 1.38
        if metric.detail:
            detail_box = renderer.textbox(slide, inner_left, details_top, inner_width, 0.38)
            renderer.write_paragraph(detail_box.text_frame, metric.detail, size=detail_size, color=colors.muted)
            renderer.fit_text_frame(detail_box.text_frame, max_size=detail_size)
            details_top += 0.34
        if metric.trend:
            trend_box = renderer.textbox(slide, inner_left, details_top, inner_width, 0.30)
            renderer.write_paragraph(trend_box.text_frame, metric.trend, size=detail_size, color=colors.accent, bold=True)
            renderer.fit_text_frame(trend_box.text_frame, max_size=detail_size, bold=True)
