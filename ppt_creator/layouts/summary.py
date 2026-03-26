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
        panel_box = renderer.panel_content_box(
            slide,
            left=panel_left,
            top=2.1,
            width=panel_width,
            height=3.2,
            padding=0.26,
        )
        tf = panel_box.text_frame
        renderer.write_paragraph(tf, "Key takeaways", size=t.eyebrow_size, color=colors.muted, bold=True, space_after=10)
        for bullet in slide_spec.bullets:
            renderer.write_paragraph(tf, f"• {bullet}", size=t.small_size + 1, color=colors.text, space_after=6)
        return

    if has_body:
        summary_box = renderer.textbox(slide, g.content_left, 2.35, g.content_width, 1.9)
        renderer.write_paragraph(
            summary_box.text_frame,
            slide_spec.body or "",
            size=t.body_size,
            color=colors.text,
        )
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
    summary_panel = renderer.panel_content_box(
        slide,
        left=g.content_left,
        top=2.2,
        width=g.content_width,
        height=3.0,
        padding=0.28,
    )
    tf = summary_panel.text_frame
    renderer.write_paragraph(tf, "Key takeaways", size=t.eyebrow_size, color=colors.muted, bold=True, space_after=10)
    for bullet in slide_spec.bullets:
        renderer.write_paragraph(tf, f"• {bullet}", size=t.body_size - 1, color=colors.text, space_after=8)