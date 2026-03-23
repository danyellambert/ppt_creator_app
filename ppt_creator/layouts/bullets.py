from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 5.4, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 6.4, 0.85)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.82, 5.8, 0.45)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)

    left_box = renderer.textbox(slide, c.margin_x, 2.55, 5.4, 2.55)
    if slide_spec.body:
        renderer.write_paragraph(left_box.text_frame, slide_spec.body, size=t.body_size, color=colors.text, space_after=8)

    for bullet in slide_spec.bullets:
        paragraph = left_box.text_frame.add_paragraph()
        paragraph.level = 0
        run = paragraph.add_run()
        run.text = f"• {bullet}"
        renderer.set_run_style(run, size=t.body_size - 1, color=colors.text)

    renderer.add_panel(slide, 8.5, 1.05, 3.75, 4.95, fill_color=colors.surface, line_color=colors.line)
    renderer.add_accent_bar(slide, 8.5, 1.05, 3.75, 0.08, color=colors.accent)

    side_box = renderer.textbox(slide, 8.88, 1.45, 2.95, 4.0)
    tf = side_box.text_frame
    renderer.write_paragraph(tf, "Executive lens", size=t.eyebrow_size, color=colors.muted, bold=True, space_after=12)
    renderer.write_paragraph(tf, "Keep decision-making crisp, reduce operational drag, and let human sellers spend more time in high-value conversations.", size=t.body_size - 1, color=colors.text, space_after=12)
    renderer.write_paragraph(tf, "What matters", size=t.small_size, color=colors.accent, bold=True, space_after=4)
    renderer.write_paragraph(tf, "• clarity\n• consistency\n• measurable lift", size=t.body_size - 1, color=colors.navy)
