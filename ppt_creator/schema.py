from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SlideType(str, Enum):
    TITLE = "title"
    SECTION = "section"
    BULLETS = "bullets"
    CARDS = "cards"
    METRICS = "metrics"
    IMAGE_TEXT = "image_text"
    CLOSING = "closing"


class CardItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    footer: str | None = None


class MetricItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    label: str
    detail: str | None = None
    trend: str | None = None


class PresentationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str | None = None
    author: str | None = None
    date: str | None = None
    theme: str = "executive_premium_minimal"


class Slide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: SlideType
    title: str | None = None
    subtitle: str | None = None
    eyebrow: str | None = None
    body: str | None = None
    bullets: list[str] = Field(default_factory=list)
    cards: list[CardItem] = Field(default_factory=list)
    metrics: list[MetricItem] = Field(default_factory=list)
    quote: str | None = None
    attribution: str | None = None
    section_label: str | None = None
    image_path: str | None = None
    image_caption: str | None = None
    speaker_notes: str | None = None

    @model_validator(mode="after")
    def validate_by_type(self) -> "Slide":
        if self.type in {SlideType.TITLE, SlideType.SECTION, SlideType.BULLETS, SlideType.CARDS, SlideType.METRICS, SlideType.IMAGE_TEXT} and not self.title:
            raise ValueError(f"slide type '{self.type.value}' requires a title")

        if self.type == SlideType.BULLETS and not (self.body or self.bullets):
            raise ValueError("bullets slide requires body or bullets")

        if self.type == SlideType.CARDS and len(self.cards) != 3:
            raise ValueError("cards slide requires exactly 3 cards")

        if self.type == SlideType.METRICS and not self.metrics:
            raise ValueError("metrics slide requires at least one metric")

        if self.type == SlideType.IMAGE_TEXT and not (self.body or self.bullets):
            raise ValueError("image_text slide requires body or bullets")

        if self.type == SlideType.CLOSING and not (self.quote or self.title):
            raise ValueError("closing slide requires quote or title")

        return self


class PresentationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    presentation: PresentationMeta
    slides: list[Slide] = Field(min_length=1)

    @classmethod
    def from_path(cls, path: str | Path) -> "PresentationInput":
        json_path = Path(path)
        return cls.model_validate(json.loads(json_path.read_text(encoding="utf-8")))
