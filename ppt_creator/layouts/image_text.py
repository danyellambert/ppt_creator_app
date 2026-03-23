from __future__ import annotations

from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.util import Inches


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    colors = renderer.theme.colors

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 4.6, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 5.4, 0.8)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.8, 5.4, 0.45)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)

    image_left = 7.1
    image_top = 1.28
    image_width = 5.15
    image_height = 4.95
    asset = renderer.resolve_asset(slide_spec.image_path)
    if asset:
        slide.shapes.add_picture(
            str(asset),
            Inches(image_left),
            Inches(image_top),
            width=Inches(image_width),
            height=Inches(image_height),
        )
    else:
        panel = renderer.add_panel(slide, image_left, image_top, image_width, image_height, fill_color=colors.surface, line_color=colors.line)
        placeholder = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            panel.left,
            panel.top,
            panel.width,
            panel.height,
        )
        placeholder.fill.solid()
        placeholder.fill.fore_color.rgb = panel.fill.fore_color.rgb
        placeholder.line.fill.background()
        box = renderer.textbox(slide, image_left + 0.55, image_top + 1.8, image_width - 1.1, 1.1)
        renderer.write_paragraph(box.text_frame, slide_spec.image_caption or "Image placeholder", size=t.body_size, color=colors.muted, bold=True)

    text_box = renderer.textbox(slide, c.margin_x, 2.45, 5.4, 3.1)
    tf = text_box.text_frame
    if slide_spec.body:
        renderer.write_paragraph(tf, slide_spec.body, size=t.body_size, color=colors.text, space_after=10)
    for bullet in slide_spec.bullets:
        paragraph = tf.add_paragraph()
        run = paragraph.add_run()
        run.text = f"• {bullet}"
        renderer.set_run_style(run, size=t.body_size - 1, color=colors.text)

    if slide_spec.image_caption and asset:
        caption_box = renderer.textbox(slide, image_left, 6.02, image_width, 0.24)
        renderer.write_paragraph(caption_box.text_frame, slide_spec.image_caption, size=t.small_size, color=colors.muted)
