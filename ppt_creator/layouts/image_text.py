from __future__ import annotations

from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from pptx.util import Inches


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    c = renderer.theme.canvas
    t = renderer.theme.typography
    components = renderer.theme.components
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "image_right")

    if slide_spec.eyebrow:
        eyebrow_box = renderer.textbox(slide, c.margin_x, 0.78, 4.6, 0.25)
        renderer.write_paragraph(eyebrow_box.text_frame, slide_spec.eyebrow.upper(), size=t.eyebrow_size, color=colors.accent, bold=True)
        renderer.fit_text_frame(eyebrow_box.text_frame, max_size=t.eyebrow_size, bold=True)

    title_box = renderer.textbox(slide, c.margin_x, 1.02, 5.4, 0.8)
    renderer.write_paragraph(title_box.text_frame, slide_spec.title or "", size=t.title_size, color=colors.navy, bold=True)
    renderer.fit_text_frame(title_box.text_frame, max_size=t.title_size, bold=True)

    if slide_spec.subtitle:
        subtitle_box = renderer.textbox(slide, c.margin_x, 1.8, 5.4, 0.45)
        renderer.write_paragraph(subtitle_box.text_frame, slide_spec.subtitle, size=t.subtitle_size, color=colors.muted)
        renderer.fit_text_frame(subtitle_box.text_frame, max_size=t.subtitle_size)

    image_left = 7.1 if variant == "image_right" else c.margin_x
    image_top = 1.28
    image_width = 5.15
    image_height = 4.95
    text_left = c.margin_x if variant == "image_right" else 7.1
    text_width = 5.4 if variant == "image_right" else 5.15
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
        renderer.add_accent_bar(slide, image_left, image_top, image_width, components.accent_bar_height, color=colors.line)
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
        heading_box = renderer.textbox(slide, image_left + 0.55, image_top + 1.55, image_width - 1.1, 0.35)
        renderer.write_paragraph(
            heading_box.text_frame,
            "Image unavailable" if slide_spec.image_path else "Image placeholder",
            size=t.body_size,
            color=colors.muted,
            bold=True,
        )
        renderer.fit_text_frame(heading_box.text_frame, max_size=t.body_size, bold=True)

        caption_box = renderer.textbox(slide, image_left + 0.55, image_top + 1.98, image_width - 1.1, 1.05)
        renderer.write_paragraph(
            caption_box.text_frame,
            slide_spec.image_caption or "Add a real image later or keep this area as a structured visual placeholder.",
            size=t.small_size + 1,
            color=colors.text,
        )
        renderer.fit_text_frame(caption_box.text_frame, max_size=t.small_size + 1)

        if slide_spec.image_path:
            path_box = renderer.textbox(slide, image_left + 0.55, image_top + 3.35, image_width - 1.1, 0.55)
            renderer.write_paragraph(
                path_box.text_frame,
                f"Missing asset: {slide_spec.image_path}",
                size=t.small_size,
                color=colors.muted,
            )
            renderer.fit_text_frame(path_box.text_frame, max_size=t.small_size)

    if slide_spec.body:
        pass

    if slide_spec.body or slide_spec.bullets:
        text_regions: list[dict[str, float | str]] = []
        if slide_spec.body:
            if slide_spec.bullets:
                text_regions.append(
                    {
                        "kind": "body",
                        "min_height": 0.82,
                        "flex": 1.0,
                        "content_weight": renderer.estimate_content_weight(body=slide_spec.body),
                    }
                )
            else:
                text_regions.append({"kind": "body", "height": 2.35})
        if slide_spec.bullets:
            text_regions.append(
                {
                    "kind": "bullets",
                    "min_height": 1.5 if slide_spec.body else 3.1,
                    "flex": 1.0,
                    "content_weight": renderer.estimate_content_weight(bullets=slide_spec.bullets),
                }
            )

        for region, (region_top, region_height) in renderer.build_content_stack(
            top=2.45,
            height=3.1,
            regions=text_regions,
            gap=0.18,
            min_flex=0.9,
            max_flex=1.35,
        ):
            if region["kind"] == "body":
                body_box = renderer.textbox(slide, text_left, region_top, text_width, region_height)
                renderer.write_paragraph(body_box.text_frame, slide_spec.body or "", size=t.body_size, color=colors.text)
                renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)
            else:
                bullets_box = renderer.textbox(slide, text_left, region_top, text_width, region_height)
                tf = bullets_box.text_frame
                for bullet in slide_spec.bullets:
                    paragraph = tf.add_paragraph()
                    run = paragraph.add_run()
                    run.text = f"• {bullet}"
                    renderer.set_run_style(run, size=t.body_size - 1, color=colors.text)
                renderer.fit_text_frame(tf, max_size=t.body_size - 1)

    if slide_spec.image_caption and asset:
        caption_box = renderer.textbox(slide, image_left, 6.02, image_width, 0.24)
        renderer.write_paragraph(caption_box.text_frame, slide_spec.image_caption, size=t.small_size, color=colors.muted)
        renderer.fit_text_frame(caption_box.text_frame, max_size=t.small_size)
