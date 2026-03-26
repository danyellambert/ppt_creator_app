"""Layout renderers for supported slide types."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ppt_creator.layouts import (
    agenda,
    bullets,
    cards,
    chart,
    closing,
    comparison,
    faq,
    image_text,
    metrics,
    section,
    summary,
    table,
    timeline,
    title,
    two_column,
)
from ppt_creator.schema import SlideType

LayoutRenderer = Callable[[Any, Any, Any, Any, int, int], None]

LAYOUT_RENDERERS: dict[SlideType, LayoutRenderer] = {
    SlideType.TITLE: title.render,
    SlideType.SECTION: section.render,
    SlideType.AGENDA: agenda.render,
    SlideType.BULLETS: bullets.render,
    SlideType.CARDS: cards.render,
    SlideType.CHART: chart.render,
    SlideType.METRICS: metrics.render,
    SlideType.IMAGE_TEXT: image_text.render,
    SlideType.TIMELINE: timeline.render,
    SlideType.COMPARISON: comparison.render,
    SlideType.TWO_COLUMN: two_column.render,
    SlideType.TABLE: table.render,
    SlideType.FAQ: faq.render,
    SlideType.SUMMARY: summary.render,
    SlideType.CLOSING: closing.render,
}

__all__ = ["LAYOUT_RENDERERS", "LayoutRenderer"]
