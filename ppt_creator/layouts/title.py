from __future__ import annotations

from pptx.util import Inches

from ppt_creator.theme import theme_display_name


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "split_panel")

    logo_asset = renderer.resolve_brand_logo(meta)
    if logo_asset and variant == "split_panel":
        slide.shapes.add_picture(
            str(logo_asset),
            Inches(g.side_panel_left + 1.0),
            Inches(0.55),
            width=Inches(2.75),
            height=Inches(0.48),
        )

    if variant == "hero_cover":
        renderer.add_accent_bar(slide, g.content_left, 0.78, g.content_width, 0.08, color=colors.accent)

        if logo_asset:
            slide.shapes.add_picture(
                str(logo_asset),
                Inches(g.content_left),
                Inches(0.55),
                width=Inches(1.8),
                height=Inches(0.34),
            )

        eyebrow_text = slide_spec.eyebrow or meta.client_name or meta.subtitle or theme_display_name(renderer.theme.name)
        if eyebrow_text:
            renderer.add_eyebrow(slide, eyebrow_text, left=g.content_left, top=1.2, width=5.0, uppercase=False)

        renderer.add_heading(
            slide,
            title=slide_spec.title or meta.title,
            subtitle=slide_spec.subtitle,
            left=g.content_left,
            top=1.55,
            width=9.0,
            subtitle_width=7.6,
            title_size=t.title_size + 8,
        )

        if slide_spec.body:
            body_box = renderer.textbox(slide, g.content_left, 3.55, 7.4, 1.1)
            renderer.write_paragraph(
                body_box.text_frame,
                slide_spec.body,
                size=t.body_size,
                color=colors.text,
            )

        highlight_panel_left = 9.35
        renderer.add_panel(
            slide,
            highlight_panel_left,
            1.6,
            2.9,
            3.7,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(slide, highlight_panel_left, 1.6, 2.9, renderer.theme.components.accent_bar_height, color=colors.navy)

        panel_box = renderer.panel_content_box(
            slide,
            left=highlight_panel_left,
            top=1.6,
            width=2.9,
            height=3.7,
            padding=0.28,
        )
        tf = panel_box.text_frame
        renderer.write_paragraph(tf, "Context", size=t.eyebrow_size, color=colors.muted, bold=True, space_after=8)
        if meta.client_name:
            renderer.write_paragraph(tf, meta.client_name, size=t.body_size, color=colors.navy, bold=True, space_after=8)
        if meta.author:
            renderer.write_paragraph(tf, meta.author, size=t.small_size + 1, color=colors.text, space_after=6)
        if meta.date:
            renderer.write_paragraph(tf, meta.date, size=t.small_size + 1, color=colors.muted, space_after=8)
        renderer.write_paragraph(tf, theme_display_name(renderer.theme.name), size=t.small_size + 1, color=colors.accent, bold=True)
        return

    renderer.add_accent_bar(slide, g.content_left, 0.72, 0.1, 1.15, color=colors.accent)

    heading_left = g.content_left + 0.33
    renderer.add_heading(
        slide,
        title=slide_spec.title or meta.title,
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or meta.subtitle,
        left=heading_left,
        top=1.25,
        width=7.8,
        subtitle_width=6.8,
        title_size=t.title_size + 6,
    )

    if slide_spec.body:
        body_box = renderer.textbox(slide, heading_left, 3.35, 5.5, 1.25)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body,
            size=t.body_size,
            color=colors.text,
        )

    renderer.add_panel(
        slide,
        g.side_panel_left + 1.0,
        1.05,
        2.75,
        4.65,
        fill_color=colors.surface,
        line_color=colors.line,
    )

    meta_box = renderer.panel_content_box(slide, left=g.side_panel_left + 1.0, top=1.05, width=2.75, height=4.65, padding=0.40)
    tf = meta_box.text_frame
    renderer.write_paragraph(tf, "DECK", size=t.eyebrow_size, color=colors.accent, bold=True, space_after=8)
    renderer.write_paragraph(tf, meta.title, size=t.body_size + 1, color=colors.navy, bold=True, space_after=12)
    if meta.client_name:
        renderer.write_paragraph(tf, "Client", size=t.small_size, color=colors.muted, bold=True, space_after=2)
        renderer.write_paragraph(tf, meta.client_name, size=t.body_size - 1, color=colors.text, space_after=10)
    if meta.author:
        renderer.write_paragraph(tf, "Author", size=t.small_size, color=colors.muted, bold=True, space_after=2)
        renderer.write_paragraph(tf, meta.author, size=t.body_size - 1, color=colors.text, space_after=10)
    if meta.date:
        renderer.write_paragraph(tf, "Date", size=t.small_size, color=colors.muted, bold=True, space_after=2)
        renderer.write_paragraph(tf, meta.date, size=t.body_size - 1, color=colors.text, space_after=10)
    renderer.write_paragraph(tf, "Theme", size=t.small_size, color=colors.muted, bold=True, space_after=2)
    renderer.write_paragraph(tf, theme_display_name(renderer.theme.name), size=t.body_size - 1, color=colors.text)
