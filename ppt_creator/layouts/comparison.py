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
    top = 2.45
    height = 3.25
    panel_bounds = renderer.build_panel_row_bounds(
        left=g.content_left,
        top=top,
        width=g.content_width,
        height=height,
        gap=gap,
        count=len(slide_spec.comparison_columns),
        min_width=3.6,
    )

    for idx, (column, (left, panel_top, panel_width, panel_height)) in enumerate(zip(slide_spec.comparison_columns, panel_bounds, strict=True)):
        accent = colors.navy if idx == 0 else colors.accent

        renderer.add_panel(
            slide,
            left,
            panel_top,
            panel_width,
            panel_height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            left,
            panel_top,
            panel_width,
            renderer.theme.components.accent_bar_height,
            color=accent,
        )

        content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
            left=left,
            top=panel_top,
            width=panel_width,
            height=panel_height,
            padding=0.28,
        )

        regions: list[dict[str, float | str]] = []
        if column.tag:
            regions.append({"kind": "tag", "height": 0.20})
        regions.append({"kind": "title", "height": 0.42})
        if column.body:
            regions.append({"kind": "body", "height": 0.82 if column.bullets else 1.48})
        if column.bullets:
            regions.append({"kind": "bullets", "min_height": 0.44, "flex": 1.0})
        if column.footer:
            regions.append({"kind": "footer", "height": 0.22})

        for region, (region_top, region_height) in renderer.stack_vertical_regions(
            top=content_top,
            height=content_height,
            regions=regions,
            gap=0.06,
        ):
            kind = region["kind"]
            if kind == "tag":
                tag_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(tag_box.text_frame, column.tag or "", size=t.small_size, color=colors.muted, bold=True)
                renderer.fit_text_frame(tag_box.text_frame, max_size=t.small_size, bold=True)
            elif kind == "title":
                title_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(title_box.text_frame, column.title, size=t.body_size + 1, color=colors.navy, bold=True)
                renderer.fit_text_frame(title_box.text_frame, max_size=t.body_size + 1, bold=True)
            elif kind == "body":
                body_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(body_box.text_frame, column.body or "", size=t.body_size - 1, color=colors.text)
                renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size - 1)
            elif kind == "bullets":
                bullets_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                tf = bullets_box.text_frame
                for bullet in column.bullets:
                    renderer.write_paragraph(tf, f"• {bullet}", size=t.small_size + 1, color=colors.text, space_after=6)
                renderer.fit_text_frame(tf, max_size=t.small_size + 1)
            elif kind == "footer":
                footer_box = renderer.textbox(slide, content_left, region_top, content_width, region_height)
                renderer.write_paragraph(footer_box.text_frame, column.footer or "", size=t.small_size, color=accent, bold=True)
                renderer.fit_text_frame(footer_box.text_frame, max_size=t.small_size, bold=True)