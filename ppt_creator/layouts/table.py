from __future__ import annotations

from pptx.enum.text import PP_ALIGN


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "Executive table",
        left=g.content_left,
        top=g.title_top,
        width=8.2,
        subtitle_width=7.0,
    )

    top = 2.15
    if slide_spec.body:
        intro_box = renderer.textbox(slide, g.content_left, top, g.content_width, 0.62)
        renderer.write_paragraph(intro_box.text_frame, slide_spec.body, size=t.body_size - 1, color=colors.text)
        top += 0.72

    columns = slide_spec.table_columns
    rows = slide_spec.table_rows
    gap = 0.06
    column_width = (g.content_width - (gap * (len(columns) - 1))) / len(columns)
    header_height = 0.48
    row_height = 0.52

    for idx, column in enumerate(columns):
        left = g.content_left + idx * (column_width + gap)
        renderer.add_panel(
            slide,
            left,
            top,
            column_width,
            header_height,
            fill_color=colors.soft_fill,
            line_color=colors.line,
        )
        header_box = renderer.textbox(slide, left + 0.06, top + 0.10, column_width - 0.12, 0.22)
        renderer.write_paragraph(
            header_box.text_frame,
            column,
            size=t.small_size + 1,
            color=colors.navy,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

    current_top = top + header_height + 0.08
    for row in rows:
        for idx, cell in enumerate(row):
            left = g.content_left + idx * (column_width + gap)
            renderer.add_panel(
                slide,
                left,
                current_top,
                column_width,
                row_height,
                fill_color=colors.surface,
                line_color=colors.line,
            )
            cell_box = renderer.textbox(slide, left + 0.06, current_top + 0.10, column_width - 0.12, 0.24)
            renderer.write_paragraph(
                cell_box.text_frame,
                cell,
                size=t.small_size + 1,
                color=colors.text,
                align=PP_ALIGN.CENTER,
            )
        current_top += row_height + 0.08