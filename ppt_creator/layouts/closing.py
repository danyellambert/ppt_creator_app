from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, g.content_left, 1.0, 0.1, 4.8, color=colors.accent)

    if slide_spec.title:
        renderer.add_eyebrow(slide, slide_spec.title, left=g.content_left + 0.43, top=1.15, width=5.0, uppercase=False)

    next_body = "Approve the narrative, connect your content pipeline, and reuse the same renderer across future decks."
    column_weights = [
        renderer.estimate_content_weight(
            title=slide_spec.title,
            body=slide_spec.quote or slide_spec.body,
            footer=slide_spec.attribution,
        ),
        renderer.estimate_content_weight(title="Next", body=next_body),
    ]
    columns = renderer.build_weighted_columns(
        left=g.content_left + 0.43,
        width=g.content_right - (g.content_left + 0.43),
        gap=0.38,
        weights=column_weights,
        min_width=2.75,
        min_flex=0.9,
        max_flex=1.35,
        kind_prefix="closing",
    )
    quote_left, quote_width = columns[0]
    panel_left, panel_width = columns[1]

    renderer.add_quote_block(
        slide,
        quote=slide_spec.quote or slide_spec.body or "",
        attribution=slide_spec.attribution,
        left=quote_left,
        top=2.0,
        width=quote_width,
        height=1.7,
    )

    panel_top = 1.55
    panel_height = 3.0
    renderer.add_panel(slide, panel_left, panel_top, panel_width, panel_height, fill_color=colors.surface, line_color=colors.line)
    for region, (content_left, region_top, content_width, region_height) in renderer.build_panel_content_stack_bounds(
        left=panel_left,
        top=panel_top,
        width=panel_width,
        height=panel_height,
        regions=[
            {"kind": "heading", "height": 0.22},
            {
                "kind": "body",
                "min_height": 1.3,
                "flex": 1.0,
                "content_weight": renderer.estimate_content_weight(body=next_body),
            },
        ],
        gap=0.10,
        padding=0.35,
        min_flex=0.9,
        max_flex=1.25,
    ):
        box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
        if region["kind"] == "heading":
            renderer.write_paragraph(box.text_frame, "Next", size=t.eyebrow_size, color=colors.accent, bold=True)
            renderer.fit_text_frame(box.text_frame, max_size=t.eyebrow_size, bold=True)
        else:
            renderer.write_paragraph(box.text_frame, next_body, size=t.body_size - 1, color=colors.text)
            renderer.fit_text_frame(box.text_frame, max_size=t.body_size - 1)
