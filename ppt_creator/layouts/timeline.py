from __future__ import annotations

from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from ppt_creator.theme import rgb


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
        width=8.0,
        subtitle_width=7.4,
    )

    items = slide_spec.timeline_items
    count = len(items)
    gap = 0.24
    item_width = (g.content_width - (gap * (count - 1))) / count
    marker_y = 2.28
    panel_top = 2.55
    panel_height = 2.9

    renderer.add_rule(
        slide,
        g.content_left + 0.18,
        marker_y,
        g.content_right - 0.18,
        marker_y,
        color=colors.line,
        width_pt=1.4,
    )

    for idx, item in enumerate(items):
        left = g.content_left + idx * (item_width + gap)
        marker_color = colors.navy if idx % 2 == 0 else colors.accent

        marker = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.OVAL,
            Inches(left + (item_width / 2) - 0.12),
            Inches(marker_y - 0.12),
            Inches(0.24),
            Inches(0.24),
        )
        marker.fill.solid()
        marker.fill.fore_color.rgb = rgb(marker_color)
        marker.line.fill.background()

        label_box = renderer.textbox(slide, left, 1.95, item_width, 0.22)
        renderer.write_paragraph(
            label_box.text_frame,
            item.tag or f"Step {idx + 1:02d}",
            size=t.small_size,
            color=colors.muted,
            bold=True,
            align=PP_ALIGN.CENTER,
        )

        renderer.add_panel(
            slide,
            left,
            panel_top,
            item_width,
            panel_height,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(
            slide,
            left,
            panel_top,
            item_width,
            renderer.theme.components.accent_bar_height,
            color=marker_color,
        )

        box = renderer.panel_content_box(
            slide,
            left=left,
            top=panel_top,
            width=item_width,
            height=panel_height,
            padding=0.22,
        )
        tf = box.text_frame
        renderer.write_paragraph(
            tf,
            item.title,
            size=t.body_size - 1,
            color=colors.navy,
            bold=True,
            space_after=8,
        )
        if item.body:
            renderer.write_paragraph(
                tf,
                item.body,
                size=t.small_size + 1,
                color=colors.text,
                space_after=8,
            )
        if item.footer:
            paragraph = renderer.write_paragraph(
                tf,
                item.footer,
                size=t.small_size,
                color=marker_color,
                bold=True,
            )
            paragraph.space_before = Pt(4)