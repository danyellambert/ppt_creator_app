from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    g = renderer.theme.grid
    t = renderer.theme.typography
    components = renderer.theme.components
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "insight_panel")
    insight_heading = slide_spec.subtitle or slide_spec.eyebrow or ""
    insight_body = slide_spec.body or (slide_spec.bullets[0] if slide_spec.bullets else "")
    insight_points = slide_spec.bullets[1:4] if len(slide_spec.bullets) > 1 else []

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 5.4, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)
        renderer.fit_text_frame(eyebrow_box.text_frame, max_size=t.eyebrow_size, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 6.4, 0.85)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)
    renderer.fit_text_frame(title_box.text_frame, max_size=t.title_size, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.82, 5.8, 0.45)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)
        renderer.fit_text_frame(subtitle_box.text_frame, max_size=t.subtitle_size)

    if variant == "insight_panel":
        split_weights = [
            renderer.estimate_content_weight(
                title=slide_spec.title,
                body=slide_spec.body,
                bullets=slide_spec.bullets,
            ),
            renderer.estimate_content_weight(
                title=insight_heading,
                body=insight_body,
                bullets=insight_points,
            ),
        ]
        split_columns = renderer.build_weighted_columns(
            left=g.content_left,
            width=g.content_width,
            gap=0.35,
            weights=split_weights,
            min_width=3.4,
            min_flex=0.9,
            max_flex=1.3,
            kind_prefix="bullets_split",
        )
        text_left, left_width = split_columns[0]
        side_left, side_width = split_columns[1]
    else:
        text_left = g.content_left
        left_width = g.content_width
        side_left = side_width = 0.0

    text_regions: list[dict[str, float | str]] = []
    if slide_spec.body:
        if slide_spec.bullets:
            text_regions.append(
                {
                    "kind": "body",
                    "min_height": 0.92,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(body=slide_spec.body),
                }
            )
        else:
            text_regions.append({"kind": "body", "height": 3.15})
    if slide_spec.bullets:
        text_regions.append(
            {
                "kind": "bullets",
                "min_height": 1.45 if slide_spec.body else 3.15,
                "flex": 1.0,
                "content_weight": renderer.estimate_content_weight(bullets=slide_spec.bullets),
            }
        )

    for region, (region_top, region_height) in renderer.build_content_stack(
        top=2.55,
        height=3.15,
        regions=text_regions,
        gap=0.18,
        min_flex=0.9,
        max_flex=1.35,
    ):
        if region["kind"] == "body":
            body_box = renderer.textbox(slide, text_left, region_top, left_width, region_height)
            renderer.write_paragraph(body_box.text_frame, slide_spec.body or "", size=t.body_size, color=colors.text)
            renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)
        else:
            bullets_box = renderer.textbox(slide, text_left, region_top, left_width, region_height)
            tf = bullets_box.text_frame
            for bullet in slide_spec.bullets:
                renderer.write_paragraph(tf, f"• {bullet}", size=t.body_size - 1, color=colors.text, space_after=6)
            renderer.fit_text_frame(tf, max_size=t.body_size - 1)

    if variant == "insight_panel":
        renderer.add_panel(slide, side_left, 1.05, side_width, 4.95, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, side_left, 1.05, side_width, components.accent_bar_height, color=colors.accent)

        side_box = renderer.textbox(slide, side_left + 0.28, 1.45, side_width - 0.56, 4.0)
        tf = side_box.text_frame
        if insight_heading:
            renderer.write_paragraph(tf, insight_heading, size=t.eyebrow_size, color=colors.muted, bold=True, space_after=12)
        if insight_body:
            renderer.write_paragraph(tf, insight_body, size=t.body_size - 1, color=colors.text, space_after=12 if insight_points else 0)
        if insight_points:
            for bullet in insight_points:
                renderer.write_paragraph(tf, f"• {bullet}", size=t.body_size - 1, color=colors.navy, space_after=4)
        renderer.fit_text_frame(tf, max_size=t.body_size - 1)
    else:
        renderer.add_rule(
            slide,
            g.content_left,
            2.22,
            g.content_right,
            2.22,
            color=colors.line,
            width_pt=1.0,
        )
        callout_text = slide_spec.subtitle or slide_spec.eyebrow or ""
        if callout_text:
            callout = renderer.textbox(slide, g.content_left, 5.9, g.content_width, 0.45)
            renderer.write_paragraph(
                callout.text_frame,
                callout_text,
                size=t.small_size + 1,
                color=colors.muted,
            )
            renderer.fit_text_frame(callout.text_frame, max_size=t.small_size + 1)
