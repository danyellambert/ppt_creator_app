from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image as PILImage
from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ppt_creator.layouts import LAYOUT_RENDERERS
from ppt_creator.schema import PresentationInput, PresentationMeta, Slide
from ppt_creator.theme import get_theme, rgb

if TYPE_CHECKING:
    from pptx.slide import Slide as PptxSlide
    from pptx.text.text import Font, TextFrame


class PresentationRenderer:
    def __init__(
        self,
        theme_name: str | None = None,
        asset_root: str | Path | None = None,
        primary_color: str | None = None,
        secondary_color: str | None = None,
    ):
        self.requested_theme_name = theme_name
        self.requested_primary_color = primary_color
        self.requested_secondary_color = secondary_color
        self.theme = get_theme(
            theme_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
        )
        self.asset_root = Path(asset_root or ".").resolve()

    def render(self, spec: PresentationInput, output_path: str | Path) -> Path:
        self.theme = get_theme(
            self.requested_theme_name or spec.presentation.theme or self.theme.name,
            primary_color=self.requested_primary_color or spec.presentation.primary_color,
            secondary_color=self.requested_secondary_color or spec.presentation.secondary_color,
        )
        destination = self.validate_output_path(output_path)
        presentation = Presentation()
        presentation.slide_width = Inches(self.theme.canvas.width)
        presentation.slide_height = Inches(self.theme.canvas.height)

        blank_layout = presentation.slide_layouts[6]
        total_slides = len(spec.slides)

        for index, slide_spec in enumerate(spec.slides, start=1):
            slide = presentation.slides.add_slide(blank_layout)
            self.apply_background(slide)
            self.render_slide(slide, slide_spec, spec.presentation, index, total_slides)
            self.add_footer(slide, spec.presentation, index, total_slides)
            self.add_speaker_notes(slide, slide_spec.speaker_notes)

        destination.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(str(destination))
        return destination

    def validate_output_path(self, output_path: str | Path) -> Path:
        destination = Path(output_path)
        if destination.suffix.lower() != ".pptx":
            raise ValueError(f"Output path must end with .pptx: {destination}")
        return destination

    def content_bounds(self) -> tuple[float, float, float]:
        grid = self.theme.grid
        return grid.content_left, grid.content_right, grid.content_width

    def resolve_layout_variant(self, slide_spec: Slide, default: str) -> str:
        return slide_spec.layout_variant or default

    def render_slide(
        self,
        slide: "PptxSlide",
        slide_spec: Slide,
        meta: PresentationMeta,
        index: int,
        total_slides: int,
    ) -> None:
        LAYOUT_RENDERERS[slide_spec.type](self, slide, slide_spec, meta, index, total_slides)

    def apply_background(self, slide: "PptxSlide") -> None:
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(self.theme.colors.background)

    def textbox(
        self,
        slide: "PptxSlide",
        left: float,
        top: float,
        width: float,
        height: float,
        *,
        margin: float = 0.0,
        vertical_anchor: MSO_ANCHOR = MSO_ANCHOR.TOP,
    ):
        shape = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        text_frame = shape.text_frame
        text_frame.clear()
        text_frame.word_wrap = True
        text_frame.vertical_anchor = vertical_anchor
        text_frame.margin_left = Pt(margin)
        text_frame.margin_right = Pt(margin)
        text_frame.margin_top = Pt(margin)
        text_frame.margin_bottom = Pt(margin)
        return shape

    def add_eyebrow(
        self,
        slide: "PptxSlide",
        text: str,
        *,
        left: float,
        top: float,
        width: float = 4.6,
        align: PP_ALIGN = PP_ALIGN.LEFT,
        uppercase: bool = True,
    ):
        shape = self.textbox(slide, left, top, width, 0.25)
        paragraph = shape.text_frame.paragraphs[0]
        paragraph.alignment = align
        run = paragraph.add_run()
        run.text = text.upper() if uppercase else text
        self.set_run_style(run, size=self.theme.typography.eyebrow_size, color=self.theme.colors.accent, bold=True)
        return shape

    def add_heading(
        self,
        slide: "PptxSlide",
        *,
        title: str,
        left: float,
        top: float,
        width: float,
        subtitle: str | None = None,
        eyebrow: str | None = None,
        title_size: int | None = None,
        subtitle_width: float | None = None,
        align: PP_ALIGN = PP_ALIGN.LEFT,
    ) -> None:
        if eyebrow:
            self.add_eyebrow(slide, eyebrow, left=left, top=top - 0.27, width=min(width, 4.8), align=align)

        title_box = self.textbox(slide, left, top, width, 0.95)
        self.write_paragraph(
            title_box.text_frame,
            title,
            size=title_size or self.theme.typography.title_size,
            color=self.theme.colors.navy,
            bold=True,
            align=align,
        )
        self.fit_text_frame(
            title_box.text_frame,
            max_size=title_size or self.theme.typography.title_size,
            bold=True,
        )

        if subtitle:
            subtitle_box = self.textbox(slide, left, top + 0.78, subtitle_width or width, 0.45)
            self.write_paragraph(
                subtitle_box.text_frame,
                subtitle,
                size=self.theme.typography.subtitle_size,
                color=self.theme.colors.muted,
                align=align,
            )
            self.fit_text_frame(
                subtitle_box.text_frame,
                max_size=self.theme.typography.subtitle_size,
            )

    def fit_text_frame(
        self,
        text_frame: "TextFrame",
        *,
        max_size: int,
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        try:
            text_frame.fit_text(
                font_family=self.theme.typography.font_name,
                max_size=max_size,
                bold=bold,
                italic=italic,
            )
        except Exception:
            return

    def panel_content_box(
        self,
        slide: "PptxSlide",
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        padding: float | None = None,
    ):
        pad = padding if padding is not None else self.theme.components.panel_padding
        return self.textbox(slide, left + pad, top + pad, width - (pad * 2), height - (pad * 2))

    def panel_inner_bounds(
        self,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        padding: float | None = None,
    ) -> tuple[float, float, float, float]:
        pad = padding if padding is not None else self.theme.components.panel_padding
        return left + pad, top + pad, width - (pad * 2), height - (pad * 2)

    def compute_cover_crop(
        self,
        *,
        image_width_px: int,
        image_height_px: int,
        box_width: float,
        box_height: float,
        focal_x: float | None = None,
        focal_y: float | None = None,
    ) -> tuple[float, float, float, float]:
        if image_width_px <= 0 or image_height_px <= 0 or box_width <= 0 or box_height <= 0:
            return 0.0, 0.0, 0.0, 0.0

        image_aspect = image_width_px / image_height_px
        box_aspect = box_width / box_height
        if abs(image_aspect - box_aspect) <= 1e-6:
            return 0.0, 0.0, 0.0, 0.0

        if image_aspect > box_aspect:
            keep_fraction = box_aspect / image_aspect
            center = 0.5 if focal_x is None else focal_x
            crop_left = min(max(0.0, center - (keep_fraction / 2.0)), 1.0 - keep_fraction)
            crop_right = max(0.0, 1.0 - keep_fraction - crop_left)
            return crop_left, 0.0, crop_right, 0.0

        keep_fraction = image_aspect / box_aspect
        center = 0.5 if focal_y is None else focal_y
        crop_top = min(max(0.0, center - (keep_fraction / 2.0)), 1.0 - keep_fraction)
        crop_bottom = max(0.0, 1.0 - keep_fraction - crop_top)
        return 0.0, crop_top, 0.0, crop_bottom

    def add_image_cover(
        self,
        slide: "PptxSlide",
        image_path: str | Path,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        focal_x: float | None = None,
        focal_y: float | None = None,
    ):
        resolved_path = Path(image_path)
        picture = slide.shapes.add_picture(
            str(resolved_path),
            Inches(left),
            Inches(top),
            width=Inches(width),
            height=Inches(height),
        )
        with PILImage.open(resolved_path) as image:
            crop_left, crop_top, crop_right, crop_bottom = self.compute_cover_crop(
                image_width_px=image.width,
                image_height_px=image.height,
                box_width=width,
                box_height=height,
                focal_x=focal_x,
                focal_y=focal_y,
            )
        picture.crop_left = crop_left
        picture.crop_top = crop_top
        picture.crop_right = crop_right
        picture.crop_bottom = crop_bottom
        return picture

    def stack_vertical_regions(
        self,
        *,
        top: float,
        height: float,
        regions: list[dict[str, float | str]],
        gap: float,
    ) -> list[tuple[dict[str, float | str], tuple[float, float]]]:
        if not regions:
            return []

        base_heights: list[float] = []
        flex_total = 0.0
        for region in regions:
            base_height = float(region.get("height") or region.get("min_height") or 0.0)
            base_heights.append(base_height)
            flex_total += float(region.get("flex") or 0.0)

        gap_total = gap * max(0, len(regions) - 1)
        remaining = max(0.0, height - sum(base_heights) - gap_total)

        bounds: list[tuple[dict[str, float | str], tuple[float, float]]] = []
        cursor_top = top
        for region, base_height in zip(regions, base_heights, strict=True):
            extra = 0.0
            if flex_total > 0 and float(region.get("flex") or 0.0) > 0:
                extra = remaining * (float(region.get("flex") or 0.0) / flex_total)
            region_height = base_height + extra
            bounds.append((region, (cursor_top, region_height)))
            cursor_top += region_height + gap
        return bounds

    def stack_horizontal_regions(
        self,
        *,
        left: float,
        width: float,
        regions: list[dict[str, float | str]],
        gap: float,
    ) -> list[tuple[dict[str, float | str], tuple[float, float]]]:
        if not regions:
            return []

        base_widths: list[float] = []
        flex_total = 0.0
        for region in regions:
            base_width = float(region.get("width") or region.get("min_width") or 0.0)
            base_widths.append(base_width)
            flex_total += float(region.get("flex") or 0.0)

        gap_total = gap * max(0, len(regions) - 1)
        remaining = max(0.0, width - sum(base_widths) - gap_total)

        bounds: list[tuple[dict[str, float | str], tuple[float, float]]] = []
        cursor_left = left
        for region, base_width in zip(regions, base_widths, strict=True):
            extra = 0.0
            if flex_total > 0 and float(region.get("flex") or 0.0) > 0:
                extra = remaining * (float(region.get("flex") or 0.0) / flex_total)
            region_width = base_width + extra
            bounds.append((region, (cursor_left, region_width)))
            cursor_left += region_width + gap
        return bounds

    def build_columns(
        self,
        *,
        left: float,
        width: float,
        gap: float,
        count: int | None = None,
        min_width: float = 0.0,
        regions: list[dict[str, float | str]] | None = None,
    ) -> list[tuple[float, float]]:
        if regions is None:
            if count is None:
                raise ValueError("build_columns requires count or regions")
            regions = [
                {"kind": f"column_{index + 1}", "min_width": min_width, "flex": 1.0}
                for index in range(count)
            ]
        return [bounds for _, bounds in self.stack_horizontal_regions(left=left, width=width, regions=regions, gap=gap)]

    def build_weighted_columns(
        self,
        *,
        left: float,
        width: float,
        gap: float,
        weights: list[float],
        min_width: float = 0.0,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
        kind_prefix: str = "column",
    ) -> list[tuple[float, float]]:
        flexes = self.normalize_content_flexes(weights, min_flex=min_flex, max_flex=max_flex)
        return self.build_columns(
            left=left,
            width=width,
            gap=gap,
            min_width=min_width,
            regions=[
                {"kind": f"{kind_prefix}_{index + 1}", "min_width": min_width, "flex": flex}
                for index, flex in enumerate(flexes)
            ],
        )

    def build_rows(
        self,
        *,
        top: float,
        height: float,
        gap: float,
        count: int | None = None,
        min_height: float = 0.0,
        regions: list[dict[str, float | str]] | None = None,
    ) -> list[tuple[float, float]]:
        if regions is None:
            if count is None:
                raise ValueError("build_rows requires count or regions")
            regions = [
                {"kind": f"row_{index + 1}", "min_height": min_height, "flex": 1.0}
                for index in range(count)
            ]
        return [bounds for _, bounds in self.stack_vertical_regions(top=top, height=height, regions=regions, gap=gap)]

    def build_weighted_rows(
        self,
        *,
        top: float,
        height: float,
        gap: float,
        weights: list[float],
        min_height: float = 0.0,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
        kind_prefix: str = "row",
    ) -> list[tuple[float, float]]:
        flexes = self.normalize_content_flexes(weights, min_flex=min_flex, max_flex=max_flex)
        return self.build_rows(
            top=top,
            height=height,
            gap=gap,
            min_height=min_height,
            regions=[
                {"kind": f"{kind_prefix}_{index + 1}", "min_height": min_height, "flex": flex}
                for index, flex in enumerate(flexes)
            ],
        )

    def build_panel_row_bounds(
        self,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        gap: float,
        count: int | None = None,
        min_width: float = 0.0,
        regions: list[dict[str, float | str]] | None = None,
    ) -> list[tuple[float, float, float, float]]:
        columns = self.build_columns(
            left=left,
            width=width,
            gap=gap,
            count=count,
            min_width=min_width,
            regions=regions,
        )
        return [(column_left, top, column_width, height) for column_left, column_width in columns]

    def build_weighted_panel_row_bounds(
        self,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        gap: float,
        weights: list[float],
        min_width: float = 0.0,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
        kind_prefix: str = "panel",
    ) -> list[tuple[float, float, float, float]]:
        columns = self.build_weighted_columns(
            left=left,
            width=width,
            gap=gap,
            weights=weights,
            min_width=min_width,
            min_flex=min_flex,
            max_flex=max_flex,
            kind_prefix=kind_prefix,
        )
        return [(column_left, top, column_width, height) for column_left, column_width in columns]

    def build_panel_grid(
        self,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        column_gap: float,
        row_gap: float,
        column_count: int | None = None,
        row_count: int | None = None,
        column_min_width: float = 0.0,
        row_min_height: float = 0.0,
        column_regions: list[dict[str, float | str]] | None = None,
        row_regions: list[dict[str, float | str]] | None = None,
    ) -> list[list[tuple[float, float, float, float]]]:
        resolved_column_regions = column_regions
        if resolved_column_regions is None:
            if column_count is None:
                raise ValueError("build_panel_grid requires column_count or column_regions")
            resolved_column_regions = [
                {"kind": f"column_{index + 1}", "min_width": column_min_width, "flex": 1.0}
                for index in range(column_count)
            ]

        resolved_row_regions = row_regions
        if resolved_row_regions is None:
            if row_count is None:
                raise ValueError("build_panel_grid requires row_count or row_regions")
            resolved_row_regions = [
                {"kind": f"row_{index + 1}", "min_height": row_min_height, "flex": 1.0}
                for index in range(row_count)
            ]

        return self.build_grid_bounds(
            left=left,
            top=top,
            width=width,
            height=height,
            column_regions=resolved_column_regions,
            row_regions=resolved_row_regions,
            column_gap=column_gap,
            row_gap=row_gap,
        )

    def estimate_content_weight(
        self,
        *,
        title: str | None = None,
        body: str | None = None,
        bullets: list[str] | None = None,
        footer: str | None = None,
        tag: str | None = None,
    ) -> float:
        bullet_items = bullets or []
        weight = 1.0
        if title:
            weight += min(0.8, len(title.split()) / 7)
        if body:
            weight += min(1.4, len(body.split()) / 18)
        if footer:
            weight += min(0.35, len(footer.split()) / 10)
        if tag:
            weight += min(0.25, len(tag.split()) / 6)
        for bullet in bullet_items:
            weight += min(0.3, len(bullet.split()) / 14)
        return weight

    def normalize_content_flexes(
        self,
        weights: list[float],
        *,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
    ) -> list[float]:
        if not weights:
            return []
        min_weight = min(weights)
        max_weight = max(weights)
        if max_weight == min_weight:
            return [1.0 for _ in weights]
        span = max_flex - min_flex
        return [
            min_flex + ((weight - min_weight) / (max_weight - min_weight)) * span
            for weight in weights
        ]

    def rebalance_flexible_regions(
        self,
        regions: list[dict[str, float | str]],
        *,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
    ) -> list[dict[str, float | str]]:
        balanced_regions = [dict(region) for region in regions]
        flexible_indices = [
            index for index, region in enumerate(balanced_regions) if float(region.get("flex") or 0.0) > 0.0
        ]
        if len(flexible_indices) <= 1:
            return balanced_regions

        weights = [
            float(balanced_regions[index].get("content_weight") or balanced_regions[index].get("flex") or 1.0)
            for index in flexible_indices
        ]
        flexes = self.normalize_content_flexes(weights, min_flex=min_flex, max_flex=max_flex)
        for index, flex in zip(flexible_indices, flexes, strict=True):
            balanced_regions[index]["flex"] = flex
            balanced_regions[index].pop("content_weight", None)
        return balanced_regions

    def build_content_stack(
        self,
        *,
        top: float,
        height: float,
        regions: list[dict[str, float | str]],
        gap: float,
        min_flex: float = 0.9,
        max_flex: float = 1.35,
    ) -> list[tuple[dict[str, float | str], tuple[float, float]]]:
        return self.stack_vertical_regions(
            top=top,
            height=height,
            regions=self.rebalance_flexible_regions(regions, min_flex=min_flex, max_flex=max_flex),
            gap=gap,
        )

    def build_grid_bounds(
        self,
        *,
        left: float,
        top: float,
        width: float,
        height: float,
        column_regions: list[dict[str, float | str]],
        row_regions: list[dict[str, float | str]],
        column_gap: float,
        row_gap: float,
    ) -> list[list[tuple[float, float, float, float]]]:
        columns = self.stack_horizontal_regions(
            left=left,
            width=width,
            regions=column_regions,
            gap=column_gap,
        )
        rows = self.stack_vertical_regions(
            top=top,
            height=height,
            regions=row_regions,
            gap=row_gap,
        )

        return [
            [
                (column_left, row_top, column_width, row_height)
                for _, (column_left, column_width) in columns
            ]
            for _, (row_top, row_height) in rows
        ]

    def add_quote_block(
        self,
        slide: "PptxSlide",
        *,
        quote: str,
        left: float,
        top: float,
        width: float,
        height: float,
        attribution: str | None = None,
    ) -> None:
        quote_box = self.textbox(slide, left, top, width, height)
        paragraph = quote_box.text_frame.paragraphs[0]
        paragraph.alignment = PP_ALIGN.LEFT
        run = paragraph.add_run()
        run.text = quote
        self.set_run_style(run, size=self.theme.typography.quote_size, color=self.theme.colors.navy, bold=True, italic=True)

        if attribution:
            attribution_box = self.textbox(slide, left, top + height + 0.3, min(width, 4.2), 0.35)
            self.write_paragraph(
                attribution_box.text_frame,
                attribution,
                size=self.theme.typography.body_size - 1,
                color=self.theme.colors.muted,
            )
            self.fit_text_frame(
                attribution_box.text_frame,
                max_size=self.theme.typography.body_size - 1,
            )

    def set_run_style(
        self,
        run,
        *,
        size: int,
        color: str,
        bold: bool = False,
        italic: bool = False,
        font_name: str | None = None,
    ) -> None:
        font = run.font
        self.set_font_style(
            font,
            size=size,
            color=color,
            bold=bold,
            italic=italic,
            font_name=font_name,
        )

    def set_font_style(
        self,
        font: "Font",
        *,
        size: int,
        color: str,
        bold: bool = False,
        italic: bool = False,
        font_name: str | None = None,
    ) -> None:
        font.name = font_name or self.theme.typography.font_name
        font.size = Pt(size)
        font.bold = bold
        font.italic = italic
        font.color.rgb = rgb(color)

    def write_paragraph(
        self,
        text_frame: "TextFrame",
        text: str,
        *,
        size: int,
        color: str,
        bold: bool = False,
        level: int = 0,
        align: PP_ALIGN = PP_ALIGN.LEFT,
        space_after: int = 0,
        italic: bool = False,
    ):
        paragraph = text_frame.paragraphs[0] if not text_frame.text and len(text_frame.paragraphs) == 1 and not text_frame.paragraphs[0].runs else text_frame.add_paragraph()
        paragraph.text = ""
        paragraph.level = level
        paragraph.alignment = align
        paragraph.space_after = Pt(space_after)
        run = paragraph.add_run()
        run.text = text
        self.set_run_style(run, size=size, color=color, bold=bold, italic=italic)
        return paragraph

    def add_rule(self, slide: "PptxSlide", x1: float, y1: float, x2: float, y2: float, *, color: str, width_pt: float = 1.25):
        line = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT,
            Inches(x1),
            Inches(y1),
            Inches(x2),
            Inches(y2),
        )
        line.line.color.rgb = rgb(color)
        line.line.width = Pt(width_pt)
        return line

    def add_panel(
        self,
        slide: "PptxSlide",
        left: float,
        top: float,
        width: float,
        height: float,
        *,
        fill_color: str,
        line_color: str,
    ):
        shape = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE,
            Inches(left),
            Inches(top),
            Inches(width),
            Inches(height),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill_color)
        shape.line.color.rgb = rgb(line_color)
        shape.line.width = Pt(self.theme.components.panel_border_width_pt)
        return shape

    def add_chart_panel(
        self,
        slide: "PptxSlide",
        left: float,
        top: float,
        width: float,
        height: float,
    ):
        return self.add_panel(
            slide,
            left,
            top,
            width,
            height,
            fill_color=self.theme.colors.surface,
            line_color=self.theme.colors.line,
        )

    def add_accent_bar(self, slide: "PptxSlide", left: float, top: float, width: float, height: float, *, color: str):
        shape = slide.shapes.add_shape(
            MSO_AUTO_SHAPE_TYPE.RECTANGLE,
            Inches(left),
            Inches(top),
            Inches(width),
            Inches(height),
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(color)
        shape.line.fill.background()
        return shape

    def add_footer(self, slide: "PptxSlide", meta: PresentationMeta, index: int, total_slides: int) -> None:
        grid = self.theme.grid
        left_text = meta.footer_text or meta.client_name or meta.author or meta.title
        if meta.date:
            left_text = f"{left_text}  •  {meta.date}" if left_text else meta.date

        left_box = self.textbox(slide, grid.content_left, grid.footer_top, 6.0, 0.2)
        left_paragraph = left_box.text_frame.paragraphs[0]
        left_paragraph.alignment = PP_ALIGN.LEFT
        left_run = left_paragraph.add_run()
        left_run.text = left_text or ""
        self.set_run_style(left_run, size=self.theme.typography.small_size, color=self.theme.colors.muted)

        right_box = self.textbox(slide, 10.9, grid.footer_top, 1.35, 0.2)
        right_paragraph = right_box.text_frame.paragraphs[0]
        right_paragraph.alignment = PP_ALIGN.RIGHT
        right_run = right_paragraph.add_run()
        right_run.text = f"{index:02d} / {total_slides:02d}"
        self.set_run_style(right_run, size=self.theme.typography.small_size, color=self.theme.colors.muted)

        self.add_rule(
            slide,
            grid.content_left,
            grid.footer_line_y,
            grid.content_right,
            grid.footer_line_y,
            color=self.theme.colors.line,
            width_pt=self.theme.components.footer_rule_width_pt,
        )

    def add_speaker_notes(self, slide: "PptxSlide", notes: str | None) -> None:
        if not notes:
            return

        notes_slide = slide.notes_slide
        text_frame = getattr(notes_slide, "notes_text_frame", None)
        if text_frame is None:
            fallback_placeholders = [placeholder for placeholder in notes_slide.placeholders if hasattr(placeholder, "text_frame")]
            if not fallback_placeholders:
                return
            text_frame = fallback_placeholders[-1].text_frame

        text_frame.clear()
        paragraph = text_frame.paragraphs[0]
        run = paragraph.add_run()
        run.text = notes.strip()
        self.set_run_style(run, size=11, color=self.theme.colors.text)

    def resolve_asset(self, image_path: str | None) -> Path | None:
        if not image_path:
            return None
        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = self.asset_root / candidate
        return candidate if candidate.exists() else None

    def resolve_brand_logo(self, meta: PresentationMeta) -> Path | None:
        return self.resolve_asset(meta.logo_path)

    def collect_missing_assets(self, spec: PresentationInput) -> list[str]:
        missing_assets: list[str] = []
        if spec.presentation.logo_path and self.resolve_brand_logo(spec.presentation) is None:
            missing_assets.append(
                f"presentation branding: missing asset '{spec.presentation.logo_path}'"
            )

        for index, slide_spec in enumerate(spec.slides, start=1):
            if not slide_spec.image_path:
                continue

            if self.resolve_asset(slide_spec.image_path) is None:
                slide_label = slide_spec.title or slide_spec.type.value
                missing_assets.append(
                    f"slide {index:02d} ({slide_label}): missing asset '{slide_spec.image_path}'"
                )
        return missing_assets


def render_presentation(
    spec: PresentationInput,
    output_path: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
) -> Path:
    renderer = PresentationRenderer(
        theme_name=theme_name,
        asset_root=asset_root,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    return renderer.render(spec, output_path)
