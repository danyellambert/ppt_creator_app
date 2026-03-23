from __future__ import annotations

from pptx.enum.text import PP_ALIGN


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, c.margin_x, 1.15, 11.6, 0.09, color=colors.navy)
    renderer.add_accent_bar(slide, c.margin_x, 5.65, 2.0, 0.09, color=colors.accent)

    label_box = renderer.textbox(slide, c.margin_x, 2.0, 4.8, 0.4)
    p = label_box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = (slide_spec.section_label or slide_spec.eyebrow or "SECTION").upper()
    renderer.set_run_style(run, size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 2.4, 7.5, 1.2)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.section_size, color=colors.navy, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 3.55, 6.2, 0.7)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)

    renderer.add_panel(slide, 10.65, 2.15, 1.55, 1.55, fill_color=colors.surface, line_color=colors.line)
    marker_box = renderer.textbox(slide, 10.88, 2.48, 1.1, 0.8)
    marker_p = marker_box.text_frame.paragraphs[0]
    marker_p.alignment = PP_ALIGN.CENTER
    marker_run = marker_p.add_run()
    marker_run.text = f"{index:02d}"
    renderer.set_run_style(marker_run, size=t.section_size - 4, color=colors.navy, bold=True)
