from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow,
        left=g.content_left,
        top=g.title_top,
        width=8.0,
        subtitle_width=7.2,
    )

    gap = 0.42
    panel_width = (g.content_width - gap) / 2
    top = 2.45
    height = 3.25

    for idx, column in enumerate(slide_spec.comparison_columns):
        left = g.content_left + idx * (panel_width + gap)
        accent = colors.navy if idx == 0 else colors.accent

        renderer.add_panel(
            slide,
            left,
            top,
            panel_width,
            height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            left,
            top,
            panel_width,
            renderer.theme.components.accent_bar_height,
            color=accent,
        )

        content_left = left + 0.28
        content_width = panel_width - 0.56
        cursor_top = top + 0.22

        if column.tag:
            tag_box = renderer.textbox(slide, content_left, cursor_top, content_width, 0.2)
            renderer.write_paragraph(
                tag_box.text_frame,
                column.tag,
                size=t.small_size,
                color=colors.muted,
                bold=True,
            )
            renderer.fit_text_frame(tag_box.text_frame, max_size=t.small_size, bold=True)
            cursor_top += 0.26

        title_box = renderer.textbox(slide, content_left, cursor_top, content_width, 0.42)
        renderer.write_paragraph(
            title_box.text_frame,
            column.title,
            size=t.body_size + 1,
            color=colors.navy,
            bold=True,
        )
        renderer.fit_text_frame(title_box.text_frame, max_size=t.body_size + 1, bold=True)
        cursor_top += 0.48

        if column.body:
            body_height = 0.82 if column.bullets else 1.48
            body_box = renderer.textbox(slide, content_left, cursor_top, content_width, body_height)
            renderer.write_paragraph(
                body_box.text_frame,
                column.body,
                size=t.body_size - 1,
                color=colors.text,
            )
            renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size - 1)
            cursor_top += body_height + 0.12

        footer_height = 0.24 if column.footer else 0.0
        available_bottom = top + height - 0.30 - footer_height
        bullets_height = max(0.44, available_bottom - cursor_top)

        if column.bullets:
            bullets_box = renderer.textbox(slide, content_left, cursor_top, content_width, bullets_height)
            tf = bullets_box.text_frame
            for bullet in column.bullets:
                renderer.write_paragraph(
                    tf,
                    f"• {bullet}",
                    size=t.small_size + 1,
                    color=colors.text,
                    space_after=6,
                )
            renderer.fit_text_frame(tf, max_size=t.small_size + 1)

        if column.footer:
            footer_box = renderer.textbox(slide, content_left, top + height - 0.34, content_width, 0.22)
            renderer.write_paragraph(
                footer_box.text_frame,
                column.footer,
                size=t.small_size,
                color=accent,
                bold=True,
            )
            renderer.fit_text_frame(footer_box.text_frame, max_size=t.small_size, bold=True)