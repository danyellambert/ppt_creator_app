from __future__ import annotations

from pptx.enum.text import PP_ALIGN


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, c.margin_x, 0.72, 0.1, 1.15, color=colors.accent)

    if slide_spec.eyebrow or meta.subtitle:
        eyebrow = renderer.textbox(slide, 1.18, 0.75, 4.0, 0.28)
        eyebrow_tf = eyebrow.text_frame
        p = eyebrow_tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = (slide_spec.eyebrow or meta.subtitle or "").upper()
        renderer.set_run_style(run, size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, 1.18, 1.25, 7.8, 1.45)
    renderer.write_paragraph(
        title_box.text_frame,
        slide_spec.title or meta.title,
        size=t.title_size + 6,
        color=colors.navy,
        bold=True,
        space_after=6,
    )

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, 1.18, 2.55, 6.8, 1.0)
        renderer.write_paragraph(
            subtitle_box.text_frame,
            slide_spec.subtitle,
            size=t.subtitle_size + 1,
            color=colors.muted,
        )

    if slide_spec.body:
        body_box = renderer.textbox(slide, 1.18, 3.35, 5.5, 1.25)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body,
            size=t.body_size,
            color=colors.text,
        )

    panel = renderer.add_panel(
        slide,
        9.5,
        1.05,
        2.75,
        4.65,
        fill_color=colors.surface,
        line_color=colors.line,
    )

    meta_box = renderer.textbox(slide, 9.9, 1.45, 1.95, 3.7)
    tf = meta_box.text_frame
    renderer.write_paragraph(tf, "DECK", size=t.eyebrow_size, color=colors.accent, bold=True, space_after=8)
    renderer.write_paragraph(tf, meta.title, size=t.body_size + 1, color=colors.navy, bold=True, space_after=12)
    if meta.author:
        renderer.write_paragraph(tf, "Author", size=t.small_size, color=colors.muted, bold=True, space_after=2)
        renderer.write_paragraph(tf, meta.author, size=t.body_size - 1, color=colors.text, space_after=10)
    if meta.date:
        renderer.write_paragraph(tf, "Date", size=t.small_size, color=colors.muted, bold=True, space_after=2)
        renderer.write_paragraph(tf, meta.date, size=t.body_size - 1, color=colors.text, space_after=10)
    renderer.write_paragraph(tf, "Theme", size=t.small_size, color=colors.muted, bold=True, space_after=2)
    renderer.write_paragraph(tf, "Executive Premium Minimal", size=t.body_size - 1, color=colors.text)
