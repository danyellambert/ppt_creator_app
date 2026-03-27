from __future__ import annotations

from pptx.util import Inches

from ppt_creator.theme import theme_display_name


def _render_meta_blocks(renderer, slide, *, left, top, width, height, blocks, typography, colors) -> None:
    if not blocks:
        return

    regions = [
        {
            "kind": f"block_{index + 1}",
            "min_height": block.get("min_height", 0.34),
            "flex": 1.0,
            "content_weight": renderer.estimate_content_weight(
                title=block.get("label"),
                body=block.get("value"),
            ),
        }
        for index, block in enumerate(blocks)
    ]

    for block, (_, (region_top, region_height)) in zip(
        blocks,
        renderer.build_content_stack(
            top=top,
            height=height,
            regions=regions,
            gap=0.08,
            min_flex=0.9,
            max_flex=1.25,
        ),
        strict=True,
    ):
        box = renderer.textbox(slide, left, region_top, width, region_height)
        tf = box.text_frame
        if block.get("label"):
            renderer.write_paragraph(
                tf,
                block["label"],
                size=typography.small_size,
                color=colors.muted,
                bold=True,
                space_after=2,
            )
        renderer.write_paragraph(
            tf,
            block["value"],
            size=block.get("size") or (typography.body_size - 1),
            color=block.get("color") or colors.text,
            bold=bool(block.get("bold", False)),
        )


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors
    variant = renderer.resolve_layout_variant(slide_spec, "split_panel")

    logo_asset = renderer.resolve_brand_logo(meta)

    if variant == "hero_cover":
        renderer.add_accent_bar(slide, g.content_left, 0.78, g.content_width, 0.08, color=colors.accent)

        eyebrow_text = slide_spec.eyebrow or meta.client_name or meta.subtitle or theme_display_name(renderer.theme.name)
        hero_columns = renderer.build_weighted_columns(
            left=g.content_left,
            width=g.content_width,
            gap=0.38,
            weights=[
                renderer.estimate_content_weight(
                    title=slide_spec.title or meta.title,
                    body=slide_spec.body,
                    footer=slide_spec.subtitle,
                    tag=eyebrow_text,
                ),
                renderer.estimate_content_weight(
                    title="Context",
                    body=" ".join(
                        part
                        for part in [meta.client_name, meta.author, meta.date, theme_display_name(renderer.theme.name)]
                        if part
                    ),
                ),
            ],
            min_width=2.75,
            min_flex=0.9,
            max_flex=1.35,
            kind_prefix="title_hero",
        )
        main_left, main_width = hero_columns[0]
        panel_left, panel_width = hero_columns[1]

        if logo_asset:
            slide.shapes.add_picture(
                str(logo_asset),
                Inches(main_left),
                Inches(0.55),
                width=Inches(1.8),
                height=Inches(0.34),
            )

        if eyebrow_text:
            renderer.add_eyebrow(slide, eyebrow_text, left=main_left, top=1.2, width=min(main_width, 5.4), uppercase=False)

        renderer.add_heading(
            slide,
            title=slide_spec.title or meta.title,
            subtitle=slide_spec.subtitle,
            left=main_left,
            top=1.55,
            width=main_width,
            subtitle_width=min(main_width, 7.6),
            title_size=t.title_size + 8,
        )

        if slide_spec.body:
            body_box = renderer.textbox(slide, main_left, 3.55, min(main_width, 7.6), 1.1)
            renderer.write_paragraph(
                body_box.text_frame,
                slide_spec.body,
                size=t.body_size,
                color=colors.text,
            )
            renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)

        renderer.add_panel(
            slide,
            panel_left,
            1.6,
            panel_width,
            3.7,
            fill_color=colors.surface,
            line_color=colors.line,
        )
        renderer.add_accent_bar(slide, panel_left, 1.6, panel_width, renderer.theme.components.accent_bar_height, color=colors.navy)

        content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
            left=panel_left,
            top=1.6,
            width=panel_width,
            height=3.7,
            padding=0.28,
        )
        _render_meta_blocks(
            renderer,
            slide,
            left=content_left,
            top=content_top,
            width=content_width,
            height=content_height,
            blocks=[
                {"value": "Context", "size": t.eyebrow_size, "color": colors.muted, "bold": True, "min_height": 0.22},
                *(
                    [{"value": meta.client_name, "size": t.body_size, "color": colors.navy, "bold": True, "min_height": 0.34}]
                    if meta.client_name
                    else []
                ),
                *(
                    [{"value": meta.author, "size": t.small_size + 1, "color": colors.text, "min_height": 0.28}]
                    if meta.author
                    else []
                ),
                *(
                    [{"value": meta.date, "size": t.small_size + 1, "color": colors.muted, "min_height": 0.28}]
                    if meta.date
                    else []
                ),
                {
                    "value": theme_display_name(renderer.theme.name),
                    "size": t.small_size + 1,
                    "color": colors.accent,
                    "bold": True,
                    "min_height": 0.28,
                },
            ],
            typography=t,
            colors=colors,
        )
        return

    renderer.add_accent_bar(slide, g.content_left, 0.72, 0.1, 1.15, color=colors.accent)

    heading_left = g.content_left + 0.33
    split_columns = renderer.build_weighted_columns(
        left=heading_left,
        width=g.content_right - heading_left,
        gap=0.42,
        weights=[
            renderer.estimate_content_weight(
                title=slide_spec.title or meta.title,
                body=slide_spec.body,
                footer=slide_spec.subtitle,
                tag=slide_spec.eyebrow or meta.subtitle,
            ),
            renderer.estimate_content_weight(
                title="Deck",
                body=" ".join(
                    part
                    for part in [meta.title, meta.client_name, meta.author, meta.date, theme_display_name(renderer.theme.name)]
                    if part
                ),
            ),
        ],
        min_width=2.75,
        min_flex=0.9,
        max_flex=1.35,
        kind_prefix="title_split",
    )
    main_left, main_width = split_columns[0]
    panel_left, panel_width = split_columns[1]

    if logo_asset:
        slide.shapes.add_picture(
            str(logo_asset),
            Inches(panel_left),
            Inches(0.55),
            width=Inches(min(2.75, panel_width)),
            height=Inches(0.48),
        )

    renderer.add_heading(
        slide,
        title=slide_spec.title or meta.title,
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or meta.subtitle,
        left=main_left,
        top=1.25,
        width=main_width,
        subtitle_width=min(main_width, 6.8),
        title_size=t.title_size + 6,
    )

    if slide_spec.body:
        body_box = renderer.textbox(slide, main_left, 3.35, min(main_width, 5.9), 1.25)
        renderer.write_paragraph(
            body_box.text_frame,
            slide_spec.body,
            size=t.body_size,
            color=colors.text,
        )
        renderer.fit_text_frame(body_box.text_frame, max_size=t.body_size)

    renderer.add_panel(
        slide,
        panel_left,
        1.05,
        panel_width,
        4.65,
        fill_color=colors.surface,
        line_color=colors.line,
    )

    content_left, content_top, content_width, content_height = renderer.panel_inner_bounds(
        left=panel_left,
        top=1.05,
        width=panel_width,
        height=4.65,
        padding=0.40,
    )
    _render_meta_blocks(
        renderer,
        slide,
        left=content_left,
        top=content_top,
        width=content_width,
        height=content_height,
        blocks=[
            {"value": "DECK", "size": t.eyebrow_size, "color": colors.accent, "bold": True, "min_height": 0.22},
            {"value": meta.title, "size": t.body_size + 1, "color": colors.navy, "bold": True, "min_height": 0.46},
            *(
                [{"label": "Client", "value": meta.client_name, "min_height": 0.52}]
                if meta.client_name
                else []
            ),
            *(
                [{"label": "Author", "value": meta.author, "min_height": 0.52}]
                if meta.author
                else []
            ),
            *(
                [{"label": "Date", "value": meta.date, "min_height": 0.52}]
                if meta.date
                else []
            ),
            {
                "label": "Theme",
                "value": theme_display_name(renderer.theme.name),
                "min_height": 0.52,
            },
        ],
        typography=t,
        colors=colors,
    )
