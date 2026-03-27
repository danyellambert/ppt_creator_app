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
        width=7.2,
    )

    top = 2.55
    gap = 0.35

    card_bounds = renderer.build_panel_row_bounds(
        left=g.content_left,
        top=top,
        width=g.content_width,
        height=2.95,
        gap=gap,
        count=len(slide_spec.cards),
        min_width=3.0,
    )

    for idx, (card, (x, panel_top, card_width, panel_height)) in enumerate(zip(slide_spec.cards, card_bounds, strict=True)):
        renderer.add_panel(slide, x, panel_top, card_width, panel_height, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, x, panel_top, card_width, renderer.theme.components.accent_bar_height, color=colors.accent if idx == 1 else colors.navy)

        content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
            left=x,
            top=panel_top,
            width=card_width,
            height=panel_height,
        )

        regions = [
            {"kind": "title", "height": 0.38},
            {"kind": "body", "min_height": 1.15, "flex": 1.0},
        ]
        if card.footer:
            regions.append({"kind": "footer", "height": 0.22})

        for region, (region_top, region_height) in renderer.stack_vertical_regions(
            top=content_top,
            height=content_height,
            regions=regions,
            gap=0.08,
        ):
            kind = region["kind"]
            if kind == "title":
                title_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(title_box.text_frame, card.title, size=t.body_size, color=colors.navy, bold=True)
                renderer.fit_text_frame(title_box.text_frame, max_size=t.body_size, bold=True)
            elif kind == "body":
                body_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(body_box.text_frame, card.body, size=t.body_size - 1, color=colors.text)
                renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size - 1)
            elif kind == "footer":
                footer_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(footer_box.text_frame, card.footer or "", size=t.small_size, color=colors.muted)
                renderer.fit_text_frame(footer_box.text_frame, max_size=t.small_size)
