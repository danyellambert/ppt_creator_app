from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 4.4, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 7.2, 0.8)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.8, 7.2, 0.4)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)

    left = c.margin_x
    top = 2.55
    card_width = 3.73
    gap = 0.35

    for idx, card in enumerate(slide_spec.cards):
        x = left + idx * (card_width + gap)
        renderer.add_panel(slide, x, top, card_width, 2.95, fill_color=colors.surface, line_color=colors.line)
        renderer.add_accent_bar(slide, x, top, card_width, 0.08, color=colors.accent if idx == 1 else colors.navy)

        box = renderer.textbox(slide, x + 0.28, top + 0.32, card_width - 0.56, 2.35)
        tf = box.text_frame
        renderer.write_paragraph(tf, card.title, size=t.body_size, color=colors.navy, bold=True, space_after=10)
        renderer.write_paragraph(tf, card.body, size=t.body_size - 1, color=colors.text, space_after=10)
        if card.footer:
            renderer.write_paragraph(tf, card.footer, size=t.small_size, color=colors.muted)
