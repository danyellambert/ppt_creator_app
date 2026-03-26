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

    left = g.content_left
    top = 2.55
    card_width = 3.73
    gap = 0.35

    for idx, card in enumerate(slide_spec.cards):
        x = left + idx * (card_width + gap)
        renderer.add_panel(slide, x, top, card_width, 2.95, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, x, top, card_width, renderer.theme.components.accent_bar_height, color=colors.accent if idx == 1 else colors.navy)

        box = renderer.panel_content_box(slide, left=x, top=top, width=card_width, height=2.95)
        tf = box.text_frame
        renderer.write_paragraph(tf, card.title, size=t.body_size, color=colors.navy, bold=True, space_after=10)
        renderer.write_paragraph(tf, card.body, size=t.body_size - 1, color=colors.text, space_after=10)
        if card.footer:
            renderer.write_paragraph(tf, card.footer, size=t.small_size, color=colors.muted)
