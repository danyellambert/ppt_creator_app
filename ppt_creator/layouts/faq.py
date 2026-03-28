from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "FAQ",
        left=g.content_left,
        top=g.title_top,
        width=8.0,
        subtitle_width=7.0,
    )

    items = slide_spec.faq_items
    columns = 2 if len(items) > 1 else 1
    panel_gap = 0.35
    panel_height = 1.35
    top_start = 2.25
    row_count = (len(items) + columns - 1) // columns
    total_height = 3.15 if row_count > 1 else 1.55
    row_flexes = renderer.normalize_content_flexes(
        [
            max(
                renderer.estimate_content_weight(title=item.title, body=item.body)
                for item in items[row_index * columns : (row_index + 1) * columns]
            )
            for row_index in range(row_count)
        ],
        min_flex=0.9,
        max_flex=1.35,
    )
    column_weights = [
        max(
            renderer.estimate_content_weight(title=item.title, body=item.body)
            for item in items[column_index::columns]
        )
        for column_index in range(columns)
    ]
    grid_bounds = renderer.build_weighted_panel_grid(
        left=g.content_left,
        top=top_start,
        width=g.content_width,
        height=total_height,
        column_gap=panel_gap,
        row_gap=0.24,
        column_weights=column_weights,
        row_weights=[max(1.0, flex) for flex in row_flexes],
        column_min_width=3.2,
        row_min_height=1.15,
        min_flex=0.9,
        max_flex=1.35,
        column_kind_prefix="faq_column",
        row_kind_prefix="faq_row",
    )

    for idx, item in enumerate(items):
        row = idx // 2
        col = idx % 2
        left, top, panel_width, panel_height = grid_bounds[row][col]

        renderer.add_panel(
            slide,
            left,
            top,
            panel_width,
            panel_height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            left,
            top,
            panel_width,
            renderer.theme.components.accent_bar_height,
            color=colors.accent if idx % 2 else colors.navy,
        )

        for region, (content_left, region_top, content_width, region_height) in renderer.build_panel_content_stack_bounds(
            left=left,
            top=top,
            width=panel_width,
            height=panel_height,
            regions=[
                {"kind": "title", "height": 0.28},
                {
                    "kind": "body",
                    "min_height": 0.68,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(body=item.body),
                },
            ],
            gap=0.06,
            padding=0.22,
            min_flex=0.9,
            max_flex=1.35,
        ):
            if region["kind"] == "title":
                title_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(
                    title_box.text_frame,
                    item.title,
                    size=t.small_size + 2,
                    color=colors.navy,
                    bold=True,
                )
                renderer.fit_text_frame(title_box.text_frame, max_size=t.small_size + 2, bold=True)
            else:
                body_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(
                    body_box.text_frame,
                    item.body,
                    size=t.small_size + 1,
                    color=colors.text,
                )
                renderer.fit_text_frame(body_box.text_frame, max_size=t.small_size + 1)