from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageDraw, ImageFont

from ppt_creator.qa import review_presentation
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput, PresentationMeta, Slide, SlideType
from ppt_creator.theme import get_theme

PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720
THUMBNAIL_WIDTH = 320
THUMBNAIL_HEIGHT = 180
CONTACT_SHEET_COLUMNS = 3


def _risk_badge_fill(*, status: str | None, risk_level: str | None) -> tuple[int, int, int]:
    if risk_level == "high" or status == "attention":
        return (184, 103, 87)
    if risk_level == "medium" or status == "review":
        return (176, 139, 91)
    return (97, 114, 135)


def find_office_runtime() -> str | None:
    for candidate in ("soffice", "libreoffice"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _rgb_tuple(hex_value: str) -> tuple[int, int, int]:
    normalized = hex_value.replace("#", "")
    return tuple(int(normalized[i : i + 2], 16) for i in (0, 2, 4))


def _safe_basename(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return normalized or "deck_preview"


def _truncate_text(value: str, *, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 3].rstrip() + "..."


def _load_font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            bbox = draw.textbbox((0, 0), candidate, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


class PreviewRenderer:
    def __init__(
        self,
        theme_name: str | None = None,
        asset_root: str | Path | None = None,
        primary_color: str | None = None,
        secondary_color: str | None = None,
        debug_grid: bool = False,
        debug_safe_areas: bool = False,
        backend: str = "auto",
    ):
        self.requested_theme_name = theme_name
        self.requested_primary_color = primary_color
        self.requested_secondary_color = secondary_color
        self.asset_root = Path(asset_root or ".").resolve()
        self.debug_grid = debug_grid
        self.debug_safe_areas = debug_safe_areas
        self.backend = backend
        self.theme = get_theme(theme_name, primary_color=primary_color, secondary_color=secondary_color)

    def render(self, spec: PresentationInput, output_dir: str | Path, *, basename: str | None = None) -> dict[str, object]:
        self.theme = get_theme(
            self.requested_theme_name or spec.presentation.theme,
            primary_color=self.requested_primary_color or spec.presentation.primary_color,
            secondary_color=self.requested_secondary_color or spec.presentation.secondary_color,
        )
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        base = basename or _safe_basename(spec.presentation.title)
        runtime = find_office_runtime() if self.backend in {"auto", "office"} else None
        backend_used = "synthetic"
        fallback_reason: str | None = None

        if self.backend == "office":
            if not runtime:
                raise RuntimeError("Office preview backend requested but no 'soffice' or 'libreoffice' executable was found")
            preview_paths = self.render_office_previews(spec, destination, base, runtime=runtime)
            backend_used = "office"
        elif self.backend == "auto" and runtime:
            try:
                preview_paths = self.render_office_previews(spec, destination, base, runtime=runtime)
                backend_used = "office"
            except Exception as exc:  # noqa: BLE001
                fallback_reason = f"Office preview unavailable, falling back to synthetic preview: {exc}"
                preview_paths = self.render_synthetic_previews(spec, destination, base)
                backend_used = "synthetic"
        else:
            if self.backend == "auto" and not runtime:
                fallback_reason = "Office runtime not found; using synthetic preview backend"
            preview_paths = self.render_synthetic_previews(spec, destination, base)

        quality_review = self.build_preview_quality_review(spec)
        contact_sheet_path = destination / f"{base}-thumbnails.png"
        self.render_contact_sheet(
            spec.presentation,
            spec.slides,
            preview_paths,
            contact_sheet_path,
            quality_review=quality_review,
        )

        return {
            "mode": "preview",
            "output_dir": str(destination),
            "preview_count": len(preview_paths),
            "previews": preview_paths,
            "thumbnail_sheet": str(contact_sheet_path),
            "quality_review": quality_review,
            "debug_grid": self.debug_grid,
            "debug_safe_areas": self.debug_safe_areas,
            "backend_requested": self.backend,
            "backend_used": backend_used,
            "backend_fallback_reason": fallback_reason,
            "office_runtime": runtime,
        }

    def render_synthetic_previews(
        self,
        spec: PresentationInput,
        destination: Path,
        base: str,
    ) -> list[str]:
        preview_paths: list[str] = []
        total_slides = len(spec.slides)
        for index, slide_spec in enumerate(spec.slides, start=1):
            image = self.render_slide(spec.presentation, slide_spec, index, total_slides)
            preview_path = destination / f"{base}-{index:02d}.png"
            image.save(preview_path)
            preview_paths.append(str(preview_path))
        return preview_paths

    def render_office_previews(
        self,
        spec: PresentationInput,
        destination: Path,
        base: str,
        *,
        runtime: str,
    ) -> list[str]:
        with TemporaryDirectory(prefix="ppt_creator_preview_") as tmpdir:
            temp_root = Path(tmpdir)
            pptx_path = temp_root / f"{base}.pptx"
            renderer = PresentationRenderer(
                theme_name=self.requested_theme_name or spec.presentation.theme,
                asset_root=self.asset_root,
                primary_color=self.requested_primary_color or spec.presentation.primary_color,
                secondary_color=self.requested_secondary_color or spec.presentation.secondary_color,
            )
            renderer.render(spec, pptx_path)

            command = [
                runtime,
                "--headless",
                "--convert-to",
                "png",
                "--outdir",
                str(temp_root),
                str(pptx_path),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                stderr = (completed.stderr or completed.stdout or "").strip()
                raise RuntimeError(stderr or f"office conversion failed with exit code {completed.returncode}")

            converted_pngs = sorted(
                path for path in temp_root.glob("*.png") if path.name != f"{base}-thumbnails.png"
            )
            if not converted_pngs:
                raise RuntimeError("office conversion did not produce PNG previews")
            if len(converted_pngs) != len(spec.slides):
                raise RuntimeError(
                    f"office conversion produced {len(converted_pngs)} PNG(s) for {len(spec.slides)} slide(s)"
                )

            preview_paths: list[str] = []
            for index, source_path in enumerate(converted_pngs, start=1):
                target_path = destination / f"{base}-{index:02d}.png"
                shutil.copy2(source_path, target_path)
                preview_paths.append(str(target_path))
            return preview_paths

    def render_slide(self, meta: PresentationMeta, slide_spec: Slide, index: int, total_slides: int) -> Image.Image:
        colors = self.theme.colors
        image = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), _rgb_tuple(colors.background))
        draw = ImageDraw.Draw(image)

        renderers = {
            SlideType.TITLE: self._render_title,
            SlideType.SECTION: self._render_section,
            SlideType.AGENDA: self._render_agenda,
            SlideType.BULLETS: self._render_bullets,
            SlideType.CARDS: self._render_cards,
            SlideType.METRICS: self._render_metrics,
            SlideType.CHART: self._render_chart,
            SlideType.IMAGE_TEXT: self._render_image_text,
            SlideType.TIMELINE: self._render_timeline,
            SlideType.COMPARISON: self._render_comparison,
            SlideType.TWO_COLUMN: self._render_two_column,
            SlideType.TABLE: self._render_table,
            SlideType.FAQ: self._render_faq,
            SlideType.SUMMARY: self._render_summary,
            SlideType.CLOSING: self._render_closing,
        }
        renderers[slide_spec.type](draw, image, slide_spec, meta)
        self._render_footer(draw, meta, index, total_slides)
        if self.debug_safe_areas or self.debug_grid:
            self._render_debug_overlay(draw)
        return image

    def render_contact_sheet(
        self,
        meta: PresentationMeta,
        slides: list[Slide],
        preview_paths: list[str],
        output_path: str | Path,
        *,
        quality_review: dict[str, object] | None = None,
    ) -> Path:
        columns = min(CONTACT_SHEET_COLUMNS, max(1, len(preview_paths)))
        rows = (len(preview_paths) + columns - 1) // columns
        card_width = THUMBNAIL_WIDTH + 40
        card_height = THUMBNAIL_HEIGHT + 68
        header_height = 108
        margin = 28
        gutter = 24

        sheet = Image.new(
            "RGB",
            (
                margin * 2 + columns * card_width + (columns - 1) * gutter,
                header_height + margin + rows * card_height + max(rows - 1, 0) * gutter + margin,
            ),
            _rgb_tuple(self.theme.colors.background),
        )
        draw = ImageDraw.Draw(sheet)
        title_font = _load_font(26, bold=True)
        subtitle_font = _load_font(16)
        card_title_font = _load_font(16, bold=True)
        card_meta_font = _load_font(13)

        draw.text((margin, 28), meta.title, fill=_rgb_tuple(self.theme.colors.navy), font=title_font)
        subtitle = meta.subtitle or meta.footer_text or meta.client_name or "Preview contact sheet"
        draw.text(
            (margin, 64),
            f"{subtitle} • {len(preview_paths)} slide(s)",
            fill=_rgb_tuple(self.theme.colors.muted),
            font=subtitle_font,
        )
        draw.line(
            (margin, header_height - 10, sheet.width - margin, header_height - 10),
            fill=_rgb_tuple(self.theme.colors.line),
            width=2,
        )

        slide_review_lookup = {
            int(review["slide_number"]): review
            for review in (quality_review or {}).get("slides", [])
        }

        for idx, preview_path in enumerate(preview_paths):
            image = Image.open(preview_path).convert("RGB")
            image.thumbnail((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
            row = idx // columns
            col = idx % columns
            x = margin + col * (card_width + gutter)
            y = header_height + row * (card_height + gutter)

            shadow_box = (x + 4, y + 6, x + card_width + 4, y + card_height + 6)
            draw.rounded_rectangle(shadow_box, radius=20, fill=(232, 235, 240))
            card_box = (x, y, x + card_width, y + card_height)
            draw.rounded_rectangle(
                card_box,
                radius=20,
                fill=_rgb_tuple(self.theme.colors.surface),
                outline=_rgb_tuple(self.theme.colors.line),
                width=2,
            )

            image_x = x + (card_width - image.width) // 2
            image_y = y + 18
            sheet.paste(image, (image_x, image_y))

            badge_box = (x + 16, y + 14, x + 58, y + 40)
            draw.rounded_rectangle(badge_box, radius=12, fill=_rgb_tuple(self.theme.colors.accent))
            draw.text((x + 28, y + 19), f"{idx + 1:02d}", fill=_rgb_tuple(self.theme.colors.surface), font=card_meta_font)

            slide_title = _truncate_text(slides[idx].title or slides[idx].type.value, max_chars=28)
            slide_type = slides[idx].type.value.replace("_", " ")
            draw.text((x + 16, y + THUMBNAIL_HEIGHT + 24), slide_title, fill=_rgb_tuple(self.theme.colors.navy), font=card_title_font)
            draw.text((x + 16, y + THUMBNAIL_HEIGHT + 46), slide_type, fill=_rgb_tuple(self.theme.colors.muted), font=card_meta_font)

            review = slide_review_lookup.get(idx + 1)
            if review:
                status = str(review.get("status") or "ok")
                risk_level = str(review.get("risk_level") or "low")
                issue_count = len(review.get("issues") or [])
                badge_fill = _risk_badge_fill(status=status, risk_level=risk_level)
                badge_text = f"{risk_level.upper()} • {issue_count}"
                badge_box = (x + card_width - 120, y + THUMBNAIL_HEIGHT + 38, x + card_width - 16, y + THUMBNAIL_HEIGHT + 60)
                draw.rounded_rectangle(badge_box, radius=10, fill=badge_fill)
                draw.text((badge_box[0] + 10, badge_box[1] + 4), badge_text, fill=(255, 255, 255), font=card_meta_font)

                overflow_regions = review.get("likely_overflow_regions") or []
                if overflow_regions:
                    overflow_text = _truncate_text(
                        ", ".join(str(region) for region in overflow_regions),
                        max_chars=34,
                    )
                    draw.text(
                        (x + 16, y + THUMBNAIL_HEIGHT + 64),
                        overflow_text,
                        fill=_rgb_tuple(self.theme.colors.muted),
                        font=_load_font(11),
                    )

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(destination)
        return destination

    def _x(self, value_in_inches: float) -> int:
        return int((value_in_inches / self.theme.canvas.width) * PREVIEW_WIDTH)

    def _y(self, value_in_inches: float) -> int:
        return int((value_in_inches / self.theme.canvas.height) * PREVIEW_HEIGHT)

    def _render_debug_overlay(self, draw: ImageDraw.ImageDraw) -> None:
        grid = self.theme.grid
        canvas = self.theme.canvas

        if self.debug_safe_areas:
            safe_box = (
                self._x(grid.content_left),
                self._y(canvas.margin_top),
                self._x(grid.content_right),
                self._y(canvas.height - canvas.margin_bottom),
            )
            draw.rounded_rectangle(safe_box, radius=10, outline=(89, 124, 250), width=3)
            draw.line(
                (
                    self._x(grid.content_left),
                    self._y(grid.footer_line_y),
                    self._x(grid.content_right),
                    self._y(grid.footer_line_y),
                ),
                fill=(89, 124, 250),
                width=2,
            )

        if self.debug_grid:
            debug_lines = [
                ("header_top", self._y(grid.header_top)),
                ("title_top", self._y(grid.title_top)),
                ("body_top", self._y(grid.body_top)),
            ]
            for label, y in debug_lines:
                draw.line((40, y, PREVIEW_WIDTH - 40, y), fill=(91, 167, 120), width=1)
                draw.text((44, y - 16), label, fill=(91, 167, 120), font=_load_font(12))

            x_guides = [
                ("content_left", self._x(grid.content_left)),
                ("content_right", self._x(grid.content_right)),
                ("side_panel_left", self._x(grid.side_panel_left)),
                ("image_left", self._x(grid.image_left)),
            ]
            for label, x in x_guides:
                draw.line((x, 30, x, PREVIEW_HEIGHT - 30), fill=(91, 167, 120), width=1)
                draw.text((x + 6, 34), label, fill=(91, 167, 120), font=_load_font(12))

    def build_preview_quality_review(self, spec: PresentationInput) -> dict[str, object]:
        return review_presentation(spec, asset_root=self.asset_root, theme_name=self.theme.name)

    def _render_heading(self, draw: ImageDraw.ImageDraw, slide_spec: Slide, *, eyebrow_default: str | None = None) -> int:
        colors = self.theme.colors
        eyebrow_font = _load_font(20, bold=True)
        title_font = _load_font(44, bold=True)
        subtitle_font = _load_font(24)

        top = 74
        eyebrow = slide_spec.eyebrow or eyebrow_default
        if eyebrow:
            draw.text((92, top), eyebrow.upper(), fill=_rgb_tuple(colors.accent), font=eyebrow_font)
            top += 34

        draw.text((92, top), slide_spec.title or "", fill=_rgb_tuple(colors.navy), font=title_font)
        top += 58
        if slide_spec.subtitle:
            draw.text((92, top), slide_spec.subtitle, fill=_rgb_tuple(colors.muted), font=subtitle_font)
            top += 38
        return top

    def _render_footer(self, draw: ImageDraw.ImageDraw, meta: PresentationMeta, index: int, total_slides: int) -> None:
        colors = self.theme.colors
        font = _load_font(16)
        draw.line((92, 660, 1188, 660), fill=_rgb_tuple(colors.line), width=2)
        left_text = meta.footer_text or meta.client_name or meta.author or meta.title
        if meta.date:
            left_text = f"{left_text} • {meta.date}" if left_text else meta.date
        draw.text((92, 672), left_text or "", fill=_rgb_tuple(colors.muted), font=font)
        draw.text((1080, 672), f"{index:02d} / {total_slides:02d}", fill=_rgb_tuple(colors.muted), font=font)

    def _draw_panel(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
        colors = self.theme.colors
        draw.rounded_rectangle(box, radius=18, fill=_rgb_tuple(colors.surface), outline=_rgb_tuple(colors.line), width=2)

    def _draw_text_block(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        box: tuple[int, int, int, int],
        *,
        font: ImageFont.ImageFont,
        fill: tuple[int, int, int],
        line_gap: int = 8,
    ) -> None:
        lines = _wrap_text(draw, text, font, box[2] - box[0])
        y = box[1]
        for line in lines:
            draw.text((box[0], y), line, fill=fill, font=font)
            y += font.size + line_gap if hasattr(font, "size") else 20 + line_gap
            if y > box[3]:
                break

    def _render_title(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        colors = self.theme.colors
        variant = slide_spec.layout_variant or "split_panel"
        if variant == "hero_cover":
            draw.rectangle((92, 72, 1188, 82), fill=_rgb_tuple(colors.accent))
            top = self._render_heading(draw, slide_spec, eyebrow_default=meta.client_name or meta.subtitle)
            if slide_spec.body:
                body_font = _load_font(24)
                self._draw_text_block(draw, slide_spec.body, (92, top + 20, 780, 470), font=body_font, fill=_rgb_tuple(colors.text))
            self._draw_panel(draw, (900, 150, 1188, 460))
            panel_title = _load_font(18, bold=True)
            body_font = _load_font(22, bold=True)
            small_font = _load_font(18)
            draw.text((928, 178), "CONTEXT", fill=_rgb_tuple(colors.muted), font=panel_title)
            if meta.client_name:
                draw.text((928, 220), meta.client_name, fill=_rgb_tuple(colors.navy), font=body_font)
            if meta.author:
                draw.text((928, 272), meta.author, fill=_rgb_tuple(colors.text), font=small_font)
            if meta.date:
                draw.text((928, 306), meta.date, fill=_rgb_tuple(colors.muted), font=small_font)
            draw.text((928, 346), self.theme.name.replace("_", " ").title(), fill=_rgb_tuple(colors.accent), font=small_font)
            return

        draw.rectangle((92, 88, 104, 236), fill=_rgb_tuple(colors.accent))
        top = self._render_heading(draw, slide_spec, eyebrow_default=meta.subtitle)
        if slide_spec.body:
            body_font = _load_font(24)
            self._draw_text_block(draw, slide_spec.body, (128, top + 30, 720, 470), font=body_font, fill=_rgb_tuple(colors.text))
        self._draw_panel(draw, (860, 120, 1170, 470))
        small_font = _load_font(16, bold=True)
        body_font = _load_font(22, bold=True)
        text_font = _load_font(18)
        y = 152
        draw.text((890, y), "DECK", fill=_rgb_tuple(colors.accent), font=small_font)
        y += 36
        draw.text((890, y), meta.title, fill=_rgb_tuple(colors.navy), font=body_font)
        y += 52
        if meta.client_name:
            draw.text((890, y), "Client", fill=_rgb_tuple(colors.muted), font=small_font)
            y += 28
            draw.text((890, y), meta.client_name, fill=_rgb_tuple(colors.text), font=text_font)
            y += 40
        if meta.author:
            draw.text((890, y), "Author", fill=_rgb_tuple(colors.muted), font=small_font)
            y += 28
            draw.text((890, y), meta.author, fill=_rgb_tuple(colors.text), font=text_font)

    def _render_section(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        colors = self.theme.colors
        title_font = _load_font(54, bold=True)
        label_font = _load_font(22, bold=True)
        subtitle_font = _load_font(24)
        if slide_spec.section_label:
            draw.text((92, 170), slide_spec.section_label.upper(), fill=_rgb_tuple(colors.accent), font=label_font)
        draw.text((92, 245), slide_spec.title or "", fill=_rgb_tuple(colors.navy), font=title_font)
        if slide_spec.subtitle:
            draw.text((92, 320), slide_spec.subtitle, fill=_rgb_tuple(colors.muted), font=subtitle_font)
        draw.rectangle((92, 382, 430, 392), fill=_rgb_tuple(colors.accent))

    def _render_agenda(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        top = self._render_heading(draw, slide_spec, eyebrow_default="Agenda") + 18
        if slide_spec.body:
            self._draw_text_block(draw, slide_spec.body, (92, top, 1188, top + 70), font=_load_font(22), fill=_rgb_tuple(self.theme.colors.text))
            top += 82
        for idx, bullet in enumerate(slide_spec.bullets, start=1):
            box = (92, top, 1188, top + 50)
            self._draw_panel(draw, box)
            draw.rectangle((92, top, 106, top + 50), fill=_rgb_tuple(self.theme.colors.accent if idx == 1 else self.theme.colors.navy))
            draw.text((128, top + 12), f"{idx:02d}", fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(18, bold=True))
            draw.text((186, top + 12), bullet, fill=_rgb_tuple(self.theme.colors.text), font=_load_font(20, bold=idx == 1))
            top += 66

    def _render_bullets(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        top = self._render_heading(draw, slide_spec) + 18
        if slide_spec.body:
            self._draw_text_block(draw, slide_spec.body, (92, top, 780, top + 110), font=_load_font(22), fill=_rgb_tuple(self.theme.colors.text))
            top += 100
        for bullet in slide_spec.bullets:
            draw.text((112, top), f"• {bullet}", fill=_rgb_tuple(self.theme.colors.text), font=_load_font(22))
            top += 42

    def _render_cards(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec)
        positions = [(92, 210, 430, 470), (472, 210, 810, 470), (852, 210, 1190, 470)]
        for box, card in zip(positions, slide_spec.cards, strict=True):
            self._draw_panel(draw, box)
            draw.text((box[0] + 24, box[1] + 24), card.title, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(24, bold=True))
            self._draw_text_block(draw, card.body, (box[0] + 24, box[1] + 70, box[2] - 24, box[3] - 60), font=_load_font(18), fill=_rgb_tuple(self.theme.colors.text))
            if card.footer:
                draw.text((box[0] + 24, box[3] - 34), card.footer, fill=_rgb_tuple(self.theme.colors.accent), font=_load_font(16, bold=True))

    def _render_metrics(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec)
        metrics = slide_spec.metrics
        gap = 24
        width = (1096 - gap * (len(metrics) - 1)) // len(metrics)
        for idx, metric in enumerate(metrics):
            left = 92 + idx * (width + gap)
            box = (left, 250, left + width, 450)
            self._draw_panel(draw, box)
            draw.rectangle((left, 250, left + width, 260), fill=_rgb_tuple(self.theme.colors.navy if idx % 2 == 0 else self.theme.colors.accent))
            draw.text((left + 24, 288), metric.value, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(30, bold=True))
            draw.text((left + 24, 336), metric.label, fill=_rgb_tuple(self.theme.colors.text), font=_load_font(18, bold=True))
            if metric.trend:
                draw.text((left + 24, 402), metric.trend, fill=_rgb_tuple(self.theme.colors.accent), font=_load_font(16, bold=True))

    def _render_chart(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        top = self._render_heading(draw, slide_spec, eyebrow_default="Data view") + 24
        if slide_spec.body:
            self._draw_text_block(draw, slide_spec.body, (92, top, 1188, top + 70), font=_load_font(20), fill=_rgb_tuple(self.theme.colors.text))
            top += 80
        box = (92, top, 1188, 560)
        self._draw_panel(draw, box)
        self._draw_chart_area(draw, slide_spec, box)

    def _draw_chart_area(self, draw: ImageDraw.ImageDraw, slide_spec: Slide, box: tuple[int, int, int, int]) -> None:
        colors = self.theme.colors
        palette = [colors.navy, colors.accent, colors.text, colors.muted]
        left, top, right, bottom = box
        chart_left = left + 56
        chart_top = top + 30
        chart_right = right - 36
        chart_bottom = bottom - 64

        draw.line((chart_left, chart_top, chart_left, chart_bottom), fill=_rgb_tuple(colors.line), width=2)
        draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill=_rgb_tuple(colors.line), width=2)

        max_value = max(max(series.values) for series in slide_spec.chart_series) or 1
        category_count = len(slide_spec.chart_categories)
        series_count = len(slide_spec.chart_series)
        variant = slide_spec.layout_variant or "column"
        label_font = _load_font(15)

        if variant == "line":
            step_x = (chart_right - chart_left) / max(category_count - 1, 1)
            for series_index, series in enumerate(slide_spec.chart_series):
                points: list[tuple[float, float]] = []
                for idx, value in enumerate(series.values):
                    x = chart_left + idx * step_x
                    y = chart_bottom - ((value / max_value) * (chart_bottom - chart_top - 18))
                    points.append((x, y))
                draw.line(points, fill=_rgb_tuple(palette[series_index % len(palette)]), width=4)
                for x, y in points:
                    draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=_rgb_tuple(palette[series_index % len(palette)]))
            for idx, category in enumerate(slide_spec.chart_categories):
                x = chart_left + idx * step_x
                draw.text((x - 14, chart_bottom + 12), category, fill=_rgb_tuple(colors.muted), font=label_font)
            return

        category_width = (chart_right - chart_left) / category_count
        if variant == "bar":
            row_height = (chart_bottom - chart_top) / category_count
            for idx, category in enumerate(slide_spec.chart_categories):
                y = chart_top + idx * row_height + 10
                draw.text((chart_left - 48, y), category, fill=_rgb_tuple(colors.muted), font=label_font)
                for series_index, series in enumerate(slide_spec.chart_series):
                    value = series.values[idx]
                    bar_length = ((value / max_value) * (chart_right - chart_left - 20))
                    bar_top = y + series_index * 14
                    draw.rectangle(
                        (chart_left, bar_top, chart_left + bar_length, bar_top + 10),
                        fill=_rgb_tuple(palette[series_index % len(palette)]),
                    )
            return

        usable_width = category_width * 0.75
        series_bar_width = usable_width / series_count
        for idx, category in enumerate(slide_spec.chart_categories):
            base_x = chart_left + idx * category_width + (category_width - usable_width) / 2
            draw.text((base_x, chart_bottom + 12), category, fill=_rgb_tuple(colors.muted), font=label_font)
            for series_index, series in enumerate(slide_spec.chart_series):
                value = series.values[idx]
                bar_height = ((value / max_value) * (chart_bottom - chart_top - 18))
                x1 = base_x + series_index * series_bar_width
                x2 = x1 + series_bar_width - 6
                y1 = chart_bottom - bar_height
                draw.rectangle((x1, y1, x2, chart_bottom), fill=_rgb_tuple(palette[series_index % len(palette)]))

    def _render_image_text(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec)
        self._draw_text_block(draw, slide_spec.body or "", (92, 230, 610, 350), font=_load_font(20), fill=_rgb_tuple(self.theme.colors.text))
        top = 340
        for bullet in slide_spec.bullets:
            draw.text((112, top), f"• {bullet}", fill=_rgb_tuple(self.theme.colors.text), font=_load_font(18))
            top += 36

        box = (760, 220, 1188, 520)
        asset = self.resolve_asset(slide_spec.image_path)
        if asset:
            loaded = Image.open(asset).convert("RGB")
            loaded.thumbnail((box[2] - box[0], box[3] - box[1]))
            image.paste(loaded, (box[0], box[1]))
        else:
            self._draw_panel(draw, box)
            draw.text((box[0] + 90, box[1] + 110), "Image unavailable", fill=_rgb_tuple(self.theme.colors.muted), font=_load_font(24, bold=True))
            if slide_spec.image_path:
                draw.text((box[0] + 48, box[1] + 154), f"Missing asset: {slide_spec.image_path}", fill=_rgb_tuple(self.theme.colors.muted), font=_load_font(16))

    def _render_timeline(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec)
        y = 340
        draw.line((130, y, 1150, y), fill=_rgb_tuple(self.theme.colors.line), width=4)
        step = (1020) / max(len(slide_spec.timeline_items) - 1, 1)
        for idx, item in enumerate(slide_spec.timeline_items):
            x = 130 + idx * step
            draw.ellipse((x - 12, y - 12, x + 12, y + 12), fill=_rgb_tuple(self.theme.colors.accent if idx % 2 else self.theme.colors.navy))
            draw.text((x - 40, y + 28), item.title, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(16, bold=True))
            if item.body:
                self._draw_text_block(draw, item.body, (x - 70, y + 56, x + 90, y + 132), font=_load_font(14), fill=_rgb_tuple(self.theme.colors.text))

    def _render_comparison(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec)
        for idx, column in enumerate(slide_spec.comparison_columns):
            left = 92 + idx * 556
            box = (left, 230, left + 520, 520)
            self._draw_panel(draw, box)
            draw.rectangle((left, 230, left + 12, 520), fill=_rgb_tuple(self.theme.colors.navy if idx == 0 else self.theme.colors.accent))
            draw.text((left + 28, 252), column.title, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(22, bold=True))
            y = 294
            if column.body:
                self._draw_text_block(draw, column.body, (left + 28, y, left + 476, y + 96), font=_load_font(18), fill=_rgb_tuple(self.theme.colors.text))
                y += 96
            for bullet in column.bullets:
                draw.text((left + 28, y), f"• {bullet}", fill=_rgb_tuple(self.theme.colors.text), font=_load_font(16))
                y += 28

    def _render_two_column(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        columns = slide_spec.two_column_columns
        comparison_like = Slide.model_construct(  # type: ignore[attr-defined]
            type=slide_spec.type,
            title=slide_spec.title,
            subtitle=slide_spec.subtitle,
            eyebrow=slide_spec.eyebrow,
            comparison_columns=columns,
        )
        self._render_comparison(draw, image, comparison_like, meta)

    def _render_table(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec, eyebrow_default="Executive table")
        left = 92
        top = 240
        total_width = 1096
        columns = len(slide_spec.table_columns)
        cell_width = total_width // columns
        for idx, column in enumerate(slide_spec.table_columns):
            box = (left + idx * cell_width, top, left + (idx + 1) * cell_width, top + 42)
            draw.rectangle(box, fill=_rgb_tuple(self.theme.colors.soft_fill), outline=_rgb_tuple(self.theme.colors.line), width=2)
            draw.text((box[0] + 16, box[1] + 10), column, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(16, bold=True))
        current_top = top + 42
        for row in slide_spec.table_rows:
            for idx, cell in enumerate(row):
                box = (left + idx * cell_width, current_top, left + (idx + 1) * cell_width, current_top + 46)
                draw.rectangle(box, fill=_rgb_tuple(self.theme.colors.surface), outline=_rgb_tuple(self.theme.colors.line), width=2)
                draw.text((box[0] + 14, box[1] + 12), cell, fill=_rgb_tuple(self.theme.colors.text), font=_load_font(16))
            current_top += 46

    def _render_faq(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        self._render_heading(draw, slide_spec, eyebrow_default="FAQ")
        positions = [(92, 232, 620, 370), (660, 232, 1188, 370), (92, 392, 620, 530), (660, 392, 1188, 530)]
        for box, item in zip(positions, slide_spec.faq_items):
            self._draw_panel(draw, box)
            draw.text((box[0] + 22, box[1] + 18), item.title, fill=_rgb_tuple(self.theme.colors.navy), font=_load_font(18, bold=True))
            self._draw_text_block(draw, item.body, (box[0] + 22, box[1] + 52, box[2] - 22, box[3] - 18), font=_load_font(16), fill=_rgb_tuple(self.theme.colors.text))

    def _render_summary(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        top = self._render_heading(draw, slide_spec, eyebrow_default="Executive summary") + 20
        if slide_spec.body:
            self._draw_text_block(draw, slide_spec.body, (92, top, 700, top + 120), font=_load_font(20), fill=_rgb_tuple(self.theme.colors.text))
        panel = (820, 220, 1188, 520)
        self._draw_panel(draw, panel)
        draw.text((848, 246), "Key takeaways", fill=_rgb_tuple(self.theme.colors.muted), font=_load_font(16, bold=True))
        y = 290
        for bullet in slide_spec.bullets:
            draw.text((848, y), f"• {bullet}", fill=_rgb_tuple(self.theme.colors.text), font=_load_font(18))
            y += 34

    def _render_closing(self, draw: ImageDraw.ImageDraw, image: Image.Image, slide_spec: Slide, meta: PresentationMeta) -> None:
        quote = slide_spec.quote or slide_spec.title or ""
        self._draw_text_block(draw, quote, (160, 220, 1120, 420), font=_load_font(34, bold=True), fill=_rgb_tuple(self.theme.colors.navy), line_gap=14)
        if slide_spec.attribution:
            draw.text((160, 450), slide_spec.attribution, fill=_rgb_tuple(self.theme.colors.muted), font=_load_font(20))

    def resolve_asset(self, image_path: str | None) -> Path | None:
        if not image_path:
            return None
        candidate = Path(image_path)
        if not candidate.is_absolute():
            candidate = self.asset_root / candidate
        return candidate if candidate.exists() else None


def render_previews(
    spec: PresentationInput,
    output_dir: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    basename: str | None = None,
    debug_grid: bool = False,
    debug_safe_areas: bool = False,
    backend: str = "auto",
) -> dict[str, object]:
    renderer = PreviewRenderer(
        theme_name=theme_name,
        asset_root=asset_root,
        primary_color=primary_color,
        secondary_color=secondary_color,
        debug_grid=debug_grid,
        debug_safe_areas=debug_safe_areas,
        backend=backend,
    )
    return renderer.render(spec, output_dir, basename=basename)
