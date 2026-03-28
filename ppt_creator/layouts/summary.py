from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    has_body = bool(slide_spec.body)
    has_bullets = bool(slide_spec.bullets)

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "Executive summary",
        left=g.content_left,
        top=g.title_top,
        width=8.0,
        subtitle_width=7.0,
    )

    if has_body and has_bullets:
        split_regions = renderer.build_constrained_columns(
            left=g.content_left,
            width=g.content_width,
            regions=[
                {
                    "kind": "narrative",
                    "min_width": 5.9,
                    "target_share": renderer.estimate_content_weight(title=slide_spec.title, body=slide_spec.body),
                },
                {
                    "kind": "panel",
                    "min_width": 3.4,
                    "max_width": 4.15,
                    "target_share": renderer.estimate_content_weight(bullets=slide_spec.bullets),
                },
            ],
            gap=0.35,
        )
        narrative_left, narrative_width = split_regions[0]
        panel_left, panel_width = split_regions[1]

        body_box = renderer.textbox(slide, narrative_left, 2.35, narrative_width, 1.55)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body or "",
            size=t.body_size,
            color=colors.text,
        )
        renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)

        panel_top = 2.1
        panel_height = 3.2
        renderer.add_panel(slide, panel_left, panel_top, panel_width, panel_height, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(
            slide,
            panel_left,
            panel_top,
            panel_width,
            renderer.theme.components.accent_bar_height,
            color=colors.accent,
        )
        panel_regions = renderer.build_constrained_panel_content_stack_bounds(
            left=panel_left,
            top=panel_top,
            width=panel_width,
            height=panel_height,
            regions=[
                {"kind": "heading", "height": 0.28},
                {
                    "kind": "bullets",
                    "min_height": 2.18,
                    "target_share": renderer.estimate_content_weight(bullets=slide_spec.bullets),
                },
            ],
            gap=0.08,
            padding=0.26,
        )
        heading_left, heading_top, heading_width, heading_height = panel_regions[0][1]
        heading_box = renderer.textbox(slide, heading_left, heading_top, heading_width, heading_height)
        renderer.write_paragraph(heading_box.text_frame, "Key takeaways", size=t.eyebrow_size, color=colors.muted, bold=True)
        renderer.fit_text_frame(heading_box.text_frame, max_size=t.eyebrow_size, bold=True)
        bullets_left, bullets_top, bullets_width, bullets_height = panel_regions[1][1]
        bullets_box = renderer.textbox(slide, bullets_left, bullets_top, bullets_width, bullets_height)
        tf = bullets_box.text_frame
        for bullet in slide_spec.bullets:
            renderer.write_paragraph(tf, f"• {bullet}", size=t.small_size + 1, color=colors.text, space_after=6)
        renderer.fit_text_frame(tf, max_size=t.small_size + 1)
        return

    if has_body:
        summary_box = renderer.textbox(slide, g.content_left, 2.35, g.content_width, 1.9)
        renderer.write_paragraph(
            summary_box.text_frame,
            slide_spec.body or "",
            size=t.body_size,
            color=colors.text,
        )
        renderer.fit_text_frame(summary_box.text_frame, max_size=t.body_size)
        return

    renderer.add_panel(
        slide,
        g.content_left,
        2.2,
        g.content_width,
        3.0,
        fill_color=colors.surface,
        line_color=colors.line,
    )
    renderer.add_accent_bar(
        slide,
        g.content_left,
        2.2,
        g.content_width,
        renderer.theme.components.accent_bar_height,
        color=colors.accent,
    )
    content_regions = renderer.build_constrained_panel_content_stack_bounds(
        left=g.content_left,
        top=2.2,
        width=g.content_width,
        height=3.0,
        regions=[
            {"kind": "heading", "height": 0.28},
            {
                "kind": "bullets",
                "min_height": 1.9,
                "target_share": renderer.estimate_content_weight(bullets=slide_spec.bullets),
            },
        ],
        gap=0.1,
        padding=0.28,
    )
    heading_left, heading_top, heading_width, heading_height = content_regions[0][1]
    heading_box = renderer.textbox(slide, heading_left, heading_top, heading_width, heading_height)
    renderer.write_paragraph(heading_box.text_frame, "Key takeaways", size=t.eyebrow_size, color=colors.muted, bold=True)
    renderer.fit_text_frame(heading_box.text_frame, max_size=t.eyebrow_size, bold=True)
    bullets_left, bullets_top, bullets_width, bullets_height = content_regions[1][1]
    bullets_box = renderer.textbox(slide, bullets_left, bullets_top, bullets_width, bullets_height)
    tf = bullets_box.text_frame
    for bullet in slide_spec.bullets:
        renderer.write_paragraph(tf, f"• {bullet}", size=t.body_size - 1, color=colors.text, space_after=8)
    renderer.fit_text_frame(tf, max_size=t.body_size - 1)