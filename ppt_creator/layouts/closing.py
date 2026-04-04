from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_accent_bar(slide, g.content_left, 0.98, 0.1, 4.95, color=colors.accent)

    title = slide_spec.title or ""
    if title:
        renderer.add_heading(
            slide,
            title=title,
            left=g.content_left + 0.43,
            top=1.12,
            width=g.content_width - 0.43,
            title_size=t.title_size + 2,
        )

    quote_text = slide_spec.quote or slide_spec.body or ""
    if not quote_text:
        return

    dense_quote = len(quote_text) > 190
    quote_left = g.content_left + 0.43
    quote_top = 2.55 if title else 1.9
    quote_width = min(g.content_width - 0.43, 8.6)
    quote_height = 2.55 if dense_quote else 2.15

    renderer.add_quote_block(
        slide,
        quote=quote_text,
        attribution=slide_spec.attribution,
        left=quote_left,
        top=quote_top,
        width=quote_width,
        height=quote_height,
    )
