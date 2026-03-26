from __future__ import annotations

from dataclasses import dataclass, replace

from pptx.dml.color import RGBColor


def rgb(hex_value: str) -> RGBColor:
    return RGBColor.from_string(hex_value.replace("#", "").upper())


def normalize_theme_color(hex_value: str | None) -> str | None:
    if hex_value is None:
        return None
    normalized = hex_value.strip().lstrip("#").upper()
    return normalized or None


def theme_display_name(name: str) -> str:
    return name.replace("_", " ").title()


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

CONSULTING_CLEAN = Theme(
    name="consulting_clean",
    canvas=CanvasTokens(),
    typography=TypographyTokens(),
    spacing=SpacingTokens(),
    grid=GridTokens(),
    colors=ColorTokens(
        background="F8FAFB",
        surface="FFFFFF",
        navy="17324A",
        text="284158",
        muted="6D7E91",
        line="D7E1EA",
        accent="7C97AF",
        soft_fill="EEF4F8",
    ),
    components=ComponentTokens(),
)

DARK_BOARDROOM = Theme(
    name="dark_boardroom",
    canvas=CanvasTokens(),
    typography=TypographyTokens(),
    spacing=SpacingTokens(),
    grid=GridTokens(),
    colors=ColorTokens(
        background="0F1723",
        surface="172233",
        navy="F3F6FB",
        text="D7E0EA",
        muted="92A3B7",
        line="32475D",
        accent="C69E70",
        soft_fill="1E2B3E",
    ),
    components=ComponentTokens(),
)

STARTUP_MINIMAL = Theme(
    name="startup_minimal",
    canvas=CanvasTokens(),
    typography=TypographyTokens(),
    spacing=SpacingTokens(),
    grid=GridTokens(),
    colors=ColorTokens(
        background="FBFBFD",
        surface="FFFFFF",
        navy="1A2343",
        text="28324C",
        muted="6F7A8E",
        line="DCE2EC",
        accent="5B7CFA",
        soft_fill="EEF2FF",
    ),
    components=ComponentTokens(),
)

THEMES = {
    EXECUTIVE_PREMIUM_MINIMAL.name: EXECUTIVE_PREMIUM_MINIMAL,
    CONSULTING_CLEAN.name: CONSULTING_CLEAN,
    DARK_BOARDROOM.name: DARK_BOARDROOM,
    STARTUP_MINIMAL.name: STARTUP_MINIMAL,
}


def get_theme(
    name: str | None,
    *,
    primary_color: str | None = None,
    secondary_color: str | None = None,
) -> Theme:
    if not name:
        theme = EXECUTIVE_PREMIUM_MINIMAL
    else:
        normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
        theme = THEMES.get(normalized, EXECUTIVE_PREMIUM_MINIMAL)

    normalized_primary = normalize_theme_color(primary_color)
    normalized_secondary = normalize_theme_color(secondary_color)

    if not normalized_primary and not normalized_secondary:
        return theme

    colors = replace(
        theme.colors,
        navy=normalized_primary or theme.colors.navy,
        accent=normalized_secondary or theme.colors.accent,
    )
    return replace(theme, colors=colors)
