from __future__ import annotations

from pptx.util import Inches

from ppt_creator.theme import theme_display_name


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    logo_asset = renderer.resolve_brand_logo(meta)
    if logo_asset:
        slide.shapes.add_picture(
            str(logo_asset),
            Inches(g.side_panel_left + 1.0),
            Inches(0.55),
            width=Inches(2.75),
            height=Inches(0.48),
        )

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
