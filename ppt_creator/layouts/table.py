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
        renderer.fit_text_frame(intro_box.text_frame, max_size=t.body_size - 1)
        top += 0.72

    columns = slide_spec.table_columns
    rows = slide_spec.table_rows
    gap = 0.06
    header_height = 0.48
    row_height = 0.52

    column_weights = [
        renderer.estimate_content_weight(
            title=column,
            body=" ".join(row[index] for row in rows if index < len(row)),
        )
        for index, column in enumerate(columns)
    ]
    column_flexes = renderer.normalize_content_flexes(
        column_weights,
        min_flex=0.85,
        max_flex=1.5,
    )
    column_regions = [
        {
            "kind": f"column_{index + 1}",
            "min_width": 1.0,
            "flex": flex,
        }
        for index, flex in enumerate(column_flexes)
    ]

    column_header_bounds = renderer.build_panel_row_content_bounds(
        left=g.content_left,
        top=top,
        width=g.content_width,
        height=header_height,
        gap=gap,
        min_width=1.0,
        regions=column_regions,
        padding=0.06,
    )

    available_rows_height = max(0.8, (g.footer_line_y - 0.22) - (top + header_height + 0.08))
    row_min_height = max(
        0.28,
        min(
            row_height,
            (available_rows_height - (0.08 * max(0, len(rows) - 1))) / max(1, len(rows)),
        ),
    )
    row_regions = [
        {
            "kind": f"row_{index + 1}",
            "min_height": row_min_height,
            "flex": flex,
        }
        for index, flex in enumerate(
            renderer.normalize_content_flexes(
                [renderer.estimate_content_weight(body=" ".join(row)) for row in rows],
                min_flex=0.9,
                max_flex=1.35,
            )
        )
    ]

    cell_grid = renderer.build_panel_grid_content_bounds(
        left=g.content_left,
        top=top + header_height + 0.08,
        width=g.content_width,
        height=available_rows_height,
        column_gap=gap,
        row_gap=0.08,
        column_regions=column_regions,
        row_regions=row_regions,
        padding=0.06,
    )

    for column, (panel_bounds, content_bounds) in zip(columns, column_header_bounds, strict=True):
        left, panel_top, column_width, panel_height = panel_bounds
        content_left, content_top, content_width, content_height = content_bounds
        renderer.add_panel(
            slide,
            left,
            panel_top,
            column_width,
            panel_height,
            fill_color=colors.soft_fill,
            line_color=colors.line,
        )
        header_box = renderer.textbox(slide, content_left, content_top, content_width, content_height)
        renderer.write_paragraph(
            header_box.text_frame,
            column,
            size=t.small_size + 1,
            color=colors.navy,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        renderer.fit_text_frame(header_box.text_frame, max_size=t.small_size + 1, bold=True)

    for row, row_cells in zip(rows, cell_grid, strict=True):
        for cell, (panel_bounds, content_bounds) in zip(row, row_cells, strict=True):
            left, panel_top, column_width, panel_height = panel_bounds
            content_left, content_top, content_width, content_height = content_bounds
            renderer.add_panel(
                slide,
                left,
                panel_top,
                column_width,
                panel_height,
                fill_color=colors.surface,
                line_color=colors.line,
            )
            cell_box = renderer.textbox(slide, content_left, content_top, content_width, content_height)
            renderer.write_paragraph(
                cell_box.text_frame,
                cell,
                size=t.small_size + 1,
                color=colors.text,
                align=PP_ALIGN.CENTER,
            )
            renderer.fit_text_frame(cell_box.text_frame, max_size=t.small_size + 1)