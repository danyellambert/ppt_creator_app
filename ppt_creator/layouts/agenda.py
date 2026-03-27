from __future__ import annotations


def render(renderer, slide, slide_spec, meta, index, total_slides) -> None:
    g = renderer.theme.grid
    t = renderer.theme.typography
    colors = renderer.theme.colors

    renderer.add_heading(
        slide,
        title=slide_spec.title or "",
        subtitle=slide_spec.subtitle,
        eyebrow=slide_spec.eyebrow or "Agenda",
        left=g.content_left,
        top=g.title_top,
        width=8.2,
        subtitle_width=7.0,
    )

    bullet_weights = [renderer.estimate_content_weight(body=bullet) for bullet in slide_spec.bullets]
    stack_regions: list[dict[str, float | str]] = []
    if slide_spec.body:
        stack_regions.append(
            {
                "kind": "intro",
                "min_height": 0.56,
                "flex": 1.0,
                "content_weight": renderer.estimate_content_weight(body=slide_spec.body),
            }
        )
    stack_regions.append(
        {
            "kind": "agenda_rows",
            "min_height": 2.6,
            "flex": 1.0,
            "content_weight": sum(bullet_weights) or 1.0,
        }
    )

    for region, (region_top, region_height) in renderer.build_content_stack(
        top=2.2,
        height=3.9,
        regions=stack_regions,
        gap=0.18,
        min_flex=0.9,
        max_flex=1.25,
    ):
        if region["kind"] == "intro":
            intro_box = renderer.textbox(slide, g.content_left, region_top, g.content_width, region_height)
            renderer.write_paragraph(
                intro_box.text_frame,
                slide_spec.body or "",
                size=t.body_size - 1,
                color=colors.text,
            )
            renderer.fit_text_frame(intro_box.text_frame, max_size=t.body_size - 1)
            continue

        row_bounds = renderer.build_weighted_rows(
            top=region_top,
            height=region_height,
            gap=0.16,
            weights=bullet_weights,
            min_height=0.46,
            min_flex=0.9,
            max_flex=1.2,
            kind_prefix="agenda_row",
        )
        for idx, (bullet, (row_top, row_height)) in enumerate(zip(slide_spec.bullets, row_bounds, strict=True), start=1):
            renderer.add_panel(
                slide,
                g.content_left,
                row_top,
                g.content_width,
                row_height,
                fill_color=colors.surface,
                line_color=colors.line,
            )
            renderer.add_accent_bar(
                slide,
                g.content_left,
                row_top,
                0.09,
                row_height,
                color=colors.accent if idx == 1 else colors.navy,
            )

            number_box = renderer.textbox(slide, g.content_left + 0.18, row_top + 0.10, 0.45, max(0.24, row_height - 0.20))
            renderer.write_paragraph(
                number_box.text_frame,
                f"{idx:02d}",
                size=t.small_size + 1,
                color=colors.accent if idx == 1 else colors.navy,
                bold=True,
            )
            renderer.fit_text_frame(number_box.text_frame, max_size=t.small_size + 1, bold=True)

            text_box = renderer.textbox(slide, g.content_left + 0.72, row_top + 0.09, g.content_width - 0.95, max(0.28, row_height - 0.18))
            renderer.write_paragraph(
                text_box.text_frame,
                bullet,
                size=t.body_size - 1,
                color=colors.text,
                bold=idx == 1,
            )
            renderer.fit_text_frame(text_box.text_frame, max_size=t.body_size - 1, bold=idx == 1)