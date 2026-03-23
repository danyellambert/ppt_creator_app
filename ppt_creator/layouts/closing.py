from __future__ import annotations

from pptx.enum.text import PP_ALIGN


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, g.content_left, 1.0, 0.1, 4.8, color=colors.accent)

    if slide_spec.title:
        renderer.add_eyebrow(slide, slide_spec.title, left=g.content_left + 0.43, top=1.15, width=5.0, uppercase=False)

    renderer.add_quote_block(
        slide,
        quote=slide_spec.quote or slide_spec.body or "",
        attribution=slide_spec.attribution,
        left=g.content_left + 0.43,
        top=2.0,
        width=8.8,
        height=1.7,
    )

    renderer.add_panel(slide, 9.2, 1.55, 3.05, 3.0, fill_color=colors.surface, line_color=colors.line)
    box = renderer.panel_content_box(slide, left=9.2, top=1.55, width=3.05, height=3.0, padding=0.35)
    tf = box.text_frame
    renderer.write_paragraph(tf, "Next", size=t.eyebrow_size, color=colors.accent, bold=True, space_after=8)
    renderer.write_paragraph(tf, "Approve the narrative, connect your content pipeline, and reuse the same renderer across future decks.", size=t.body_size - 1, color=colors.text)
