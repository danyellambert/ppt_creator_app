from __future__ import annotations

from pptx.enum.text import PP_ALIGN


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, g.content_left, 1.15, g.content_width, 0.09, color=colors.navy)
    renderer.add_accent_bar(slide, g.content_left, 5.65, 2.0, 0.09, color=colors.accent)

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.section_label or slide_spec.eyebrow or "SECTION",
        left=g.content_left,
        top=2.4,
        width=7.5,
        subtitle_width=6.2,
        title_size=t.section_size,
    )

    renderer.add_panel(slide, 10.65, 2.15, 1.55, 1.55, fill_color=colors.surface, line_color=colors.line)
    marker_box = renderer.textbox(slide, 10.88, 2.48, 1.1, 0.8)
    marker_p = marker_box.text_frame.paragraphs[0]
    marker_p.alignment = PP_ALIGN.CENTER
    marker_run = marker_p.add_run()
    marker_run.text = f"{index:02d}"
    renderer.set_run_style(marker_run, size=t.section_size - 4, color=colors.navy, bold=True)
