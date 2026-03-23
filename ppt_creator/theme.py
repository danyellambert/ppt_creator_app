from __future__ import annotations

from dataclasses import dataclass

from pptx.dml.color import RGBColor


def rgb(hex_value: str) -> RGBColor:
    return RGBColor.from_string(hex_value.replace("#", "").upper())


@dataclass(frozen=True)
class CanvasTokens:
    width: float = 13.333
    height: float = 7.5
    margin_x: float = 0.85
    margin_top: float = 0.6
    margin_bottom: float = 0.45
    gutter: float = 0.28


@dataclass(frozen=True)
class TypographyTokens:
    font_name: str = "Arial"
    title_size: int = 28
    section_size: int = 30
    subtitle_size: int = 13
    body_size: int = 15
    small_size: int = 9
    eyebrow_size: int = 10
    metric_value_size: int = 24
    metric_label_size: int = 11
    quote_size: int = 22


@dataclass(frozen=True)
class SpacingTokens:
    xs: float = 0.12
    sm: float = 0.20
    md: float = 0.32
    lg: float = 0.48
    xl: float = 0.72


@dataclass(frozen=True)
class GridTokens:
    content_left: float = 0.85
    content_right: float = 12.45
    header_top: float = 0.78
    title_top: float = 1.02
    body_top: float = 2.45
    side_panel_left: float = 8.5
    side_panel_width: float = 3.75
    image_left: float = 7.1
    image_width: float = 5.15
    footer_top: float = 6.92
    footer_line_y: float = 6.86

    @property
    def content_width(self) -> float:
        return self.content_right - self.content_left


@dataclass(frozen=True)
class ColorTokens:
    background: str = "F7F5F2"
    surface: str = "FFFDFC"
    navy: str = "14263F"
    text: str = "203247"
    muted: str = "617287"
    line: str = "D8DEE6"
    accent: str = "B08B5B"
    soft_fill: str = "EEF1F4"


@dataclass(frozen=True)
class ComponentTokens:
    panel_padding: float = 0.24
    accent_bar_height: float = 0.08
    panel_border_width_pt: float = 1.0
    footer_rule_width_pt: float = 0.8


@dataclass(frozen=True)
class Theme:
    name: str
    canvas: CanvasTokens
    typography: TypographyTokens
    spacing: SpacingTokens
    grid: GridTokens
    colors: ColorTokens
    components: ComponentTokens


EXECUTIVE_PREMIUM_MINIMAL = Theme(
    name="executive_premium_minimal",
    canvas=CanvasTokens(),
    typography=TypographyTokens(),
    spacing=SpacingTokens(),
    grid=GridTokens(),
    colors=ColorTokens(),
    components=ComponentTokens(),
)

THEMES = {
    EXECUTIVE_PREMIUM_MINIMAL.name: EXECUTIVE_PREMIUM_MINIMAL,
}


def get_theme(name: str | None) -> Theme:
    if not name:
        return EXECUTIVE_PREMIUM_MINIMAL

    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    return THEMES.get(normalized, EXECUTIVE_PREMIUM_MINIMAL)
