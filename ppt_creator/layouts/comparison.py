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

        box = renderer.panel_content_box(
            slide,
            left=left,
            top=top,
            width=panel_width,
            height=height,
            padding=0.28,
        )
        tf = box.text_frame

        if column.tag:
            renderer.write_paragraph(
                tf,
                column.tag,
                size=t.small_size,
                color=colors.muted,
                bold=True,
                space_after=6,
            )
        renderer.write_paragraph(
            tf,
            column.title,
            size=t.body_size + 1,
            color=colors.navy,
            bold=True,
            space_after=10,
        )
        if column.body:
            renderer.write_paragraph(
                tf,
                column.body,
                size=t.body_size - 1,
                color=colors.text,
                space_after=10,
            )
        for bullet in column.bullets:
            renderer.write_paragraph(
                tf,
                f"• {bullet}",
                size=t.small_size + 1,
                color=colors.text,
                space_after=6,
            )
        if column.footer:
            renderer.write_paragraph(
                tf,
                column.footer,
                size=t.small_size,
                color=accent,
                bold=True,
                space_after=0,
            )