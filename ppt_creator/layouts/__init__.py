"""Layout renderers for supported slide types."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ppt_creator.layouts import (
    bullets,
    cards,
    closing,
    comparison,
    image_text,
    metrics,
    section,
    timeline,
    title,
)
from ppt_creator.schema import SlideType

LayoutRenderer = Callable[[Any, Any, Any, Any, int, int], None]

LAYOUT_RENDERERS: dict[SlideType, LayoutRenderer] = {
    SlideType.TITLE: title.render,
    SlideType.SECTION: section.render,
    SlideType.BULLETS: bullets.render,
    SlideType.CARDS: cards.render,
    SlideType.METRICS: metrics.render,
    SlideType.IMAGE_TEXT: image_text.render,
    SlideType.TIMELINE: timeline.render,
    SlideType.COMPARISON: comparison.render,
    SlideType.CLOSING: closing.render,
}

__all__ = ["LAYOUT_RENDERERS", "LayoutRenderer"]
