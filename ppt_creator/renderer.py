from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pptx import Presentation
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from ppt_creator.schema import PresentationInput, PresentationMeta, Slide, SlideType
from ppt_creator.theme import Theme, get_theme, rgb

if TYPE_CHECKING:
    from pptx.slide import Slide as PptxSlide
    from pptx.text.text import Font, TextFrame


class PresentationRenderer:
    def __init__(self, theme_name: str | None = None, asset_root: str | Path | None = None):
        self.requested_theme_name = theme_name
        self.theme = get_theme(theme_name)
        self.asset_root = Path(asset_root or ".").resolve()

    def render(self, spec: PresentationInput, output_path: str | Path) -> Path:
        self.theme = get_theme(self.requested_theme_name or spec.presentation.theme or self.theme.name)
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

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        presentation.save(str(destination))
        return destination

    def render_slide(
        self,
        slide: "PptxSlide",
        slide_spec: Slide,
        meta: PresentationMeta,
        index: int,
        total_slides: int,
    ) -> None:
        from ppt_creator.layouts import bullets, cards, closing, image_text, metrics, section, title

        layout_map = {
            SlideType.TITLE: title.render,
            SlideType.SECTION: section.render,
            SlideType.BULLETS: bullets.render,
            SlideType.CARDS: cards.render,
            SlideType.METRICS: metrics.render,
            SlideType.IMAGE_TEXT: image_text.render,
            SlideType.CLOSING: closing.render,
        }
        layout_map[slide_spec.type](self, slide, slide_spec, meta, index, total_slides)

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
        shape.line.width = Pt(1)
        return shape

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
        c = self.theme.canvas
        left_text = meta.author or meta.title
        if meta.date:
            left_text = f"{left_text}  •  {meta.date}" if left_text else meta.date

        left_box = self.textbox(slide, c.margin_x, 6.92, 6.0, 0.2)
        left_paragraph = left_box.text_frame.paragraphs[0]
        left_paragraph.alignment = PP_ALIGN.LEFT
        left_run = left_paragraph.add_run()
        left_run.text = left_text or ""
        self.set_run_style(left_run, size=self.theme.typography.small_size, color=self.theme.colors.muted)

        right_box = self.textbox(slide, 10.9, 6.92, 1.35, 0.2)
        right_paragraph = right_box.text_frame.paragraphs[0]
        right_paragraph.alignment = PP_ALIGN.RIGHT
        right_run = right_paragraph.add_run()
        right_run.text = f"{index:02d} / {total_slides:02d}"
        self.set_run_style(right_run, size=self.theme.typography.small_size, color=self.theme.colors.muted)

        self.add_rule(slide, c.margin_x, 6.86, 12.45, 6.86, color=self.theme.colors.line, width_pt=0.8)

    def add_speaker_notes(self, slide: "PptxSlide", notes: str | None) -> None:
        if not notes:
            return

        notes_slide = slide.notes_slide
        text_frame = getattr(notes_slide, "notes_text_frame", None)
        if text_frame is None:
            text_frame = notes_slide.placeholders[1].text_frame

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


def render_presentation(
    spec: PresentationInput,
    output_path: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
) -> Path:
    renderer = PresentationRenderer(theme_name=theme_name, asset_root=asset_root)
    return renderer.render(spec, output_path)
