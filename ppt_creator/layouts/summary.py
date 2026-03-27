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
        narrative_left = g.content_left
        narrative_width = 6.9
        panel_left = 8.15
        panel_width = 4.1

        body_box = renderer.textbox(slide, narrative_left, 2.35, narrative_width, 1.55)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body or "",
            size=t.body_size,
            color=colors.text,
        )
        renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)

        renderer.add_panel(
            slide,
            panel_left,
            2.1,
            panel_width,
            3.2,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            panel_left,
            2.1,
            panel_width,
            renderer.theme.components.accent_bar_height,
            color=colors.accent,
        )
        heading_box = renderer.textbox(slide, panel_left + 0.26, 2.42, panel_width - 0.52, 0.28)
        renderer.write_paragraph(
            heading_box.text_frame,
            "Key takeaways",
            size=t.eyebrow_size,
            color=colors.muted,
            bold=True,
        )
        bullets_box = renderer.textbox(slide, panel_left + 0.26, 2.78, panel_width - 0.52, 2.18)
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
    heading_box = renderer.textbox(slide, g.content_left + 0.28, 2.52, g.content_width - 0.56, 0.28)
    renderer.write_paragraph(
        heading_box.text_frame,
        "Key takeaways",
        size=t.eyebrow_size,
        color=colors.muted,
        bold=True,
    )
    bullets_box = renderer.textbox(slide, g.content_left + 0.28, 2.9, g.content_width - 0.56, 1.9)
    tf = bullets_box.text_frame
    for bullet in slide_spec.bullets:
        renderer.write_paragraph(tf, f"• {bullet}", size=t.body_size - 1, color=colors.text, space_after=8)
    renderer.fit_text_frame(tf, max_size=t.body_size - 1)