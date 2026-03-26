from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "Agenda",
        left=g.content_left,
        top=g.title_top,
        width=8.2,
        subtitle_width=7.0,
    )

    current_top = 2.2
    if slide_spec.body:
        intro_box = renderer.textbox(slide, g.content_left, current_top, g.content_width, 0.65)
        renderer.write_paragraph(
            intro_box.text_frame,
            slide_spec.body,
            size=t.body_size - 1,
            color=colors.text,
        )
        current_top += 0.72

    row_height = 0.58
    row_gap = 0.16
    for idx, bullet in enumerate(slide_spec.bullets, start=1):
        renderer.add_panel(
            slide,
            g.content_left,
            current_top,
            g.content_width,
            row_height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            g.content_left,
            current_top,
            0.09,
            row_height,
            color=colors.accent if idx == 1 else colors.navy,
        )

        number_box = renderer.textbox(slide, g.content_left + 0.18, current_top + 0.12, 0.45, 0.22)
        renderer.write_paragraph(
            number_box.text_frame,
            f"{idx:02d}",
            size=t.small_size + 1,
            color=colors.accent if idx == 1 else colors.navy,
            bold=True,
        )

        text_box = renderer.textbox(slide, g.content_left + 0.72, current_top + 0.10, g.content_width - 0.95, 0.26)
        renderer.write_paragraph(
            text_box.text_frame,
            bullet,
            size=t.body_size - 1,
            color=colors.text,
            bold=True if idx == 1 else False,
        )
        current_top += row_height + row_gap