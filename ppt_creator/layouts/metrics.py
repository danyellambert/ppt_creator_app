from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 5.2, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 6.8, 0.8)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.8, 7.0, 0.4)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)

    metrics = slide_spec.metrics
    count = len(metrics)
    gap = 0.28
    total_width = 11.63
    card_width = (total_width - gap * (count - 1)) / count
    left = c.margin_x
    top = 2.55

    for idx, metric in enumerate(metrics):
        x = left + idx * (card_width + gap)
        renderer.add_panel(slide, x, top, card_width, 2.7, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, x, top, card_width, 0.08, color=colors.navy if idx % 2 == 0 else colors.accent)

        box = renderer.textbox(slide, x + 0.24, top + 0.28, card_width - 0.48, 2.05)
        tf = box.text_frame
        renderer.write_paragraph(tf, metric.value, size=t.metric_value_size, color=colors.navy, bold=True, space_after=6)
        renderer.write_paragraph(tf, metric.label, size=t.metric_label_size + 1, color=colors.text, bold=True, space_after=8)
        if metric.detail:
            renderer.write_paragraph(tf, metric.detail, size=t.small_size + 1, color=colors.muted, space_after=5)
        if metric.trend:
            renderer.write_paragraph(tf, metric.trend, size=t.small_size + 1, color=colors.accent, bold=True)
