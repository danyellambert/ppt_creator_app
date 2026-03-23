from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


MAX_BULLETS_PER_SLIDE = 6
MAX_METRICS_PER_SLIDE = 4


def _clean_optional_text(value: object) -> str | None | object:
    if value is None or not isinstance(value, str):
        return value

    cleaned = value.strip()
    return cleaned or None


def _clean_required_text(value: object, field_name: str) -> str | object:
    if not isinstance(value, str):
        return value

    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


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

    @field_validator("title", "body", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)

    @field_validator("footer", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class MetricItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str
    label: str
    detail: str | None = None
    trend: str | None = None

    @field_validator("value", "label", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)

    @field_validator("detail", "trend", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class PresentationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str | None = None
    author: str | None = None
    date: str | None = None
    theme: str = "executive_premium_minimal"

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("subtitle", "author", "date", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("theme", mode="before")
    @classmethod
    def normalize_theme(cls, value: object) -> str | object:
        if value is None:
            return "executive_premium_minimal"
        if not isinstance(value, str):
            return value

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized or "executive_premium_minimal"


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

    @field_validator(
        "title",
        "subtitle",
        "eyebrow",
        "body",
        "quote",
        "attribution",
        "section_label",
        "image_path",
        "image_caption",
        "speaker_notes",
        mode="before",
    )
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("bullets")
    @classmethod
    def clean_bullets(cls, bullets: list[str]) -> list[str]:
        cleaned: list[str] = []
        for index, bullet in enumerate(bullets, start=1):
            if not isinstance(bullet, str):
                raise ValueError(f"bullet #{index} must be a string")

            value = bullet.strip()
            if not value:
                raise ValueError(f"bullet #{index} cannot be empty")
            cleaned.append(value)
        return cleaned

    @model_validator(mode="after")
    def validate_by_type(self) -> "Slide":
        if self.type in {SlideType.TITLE, SlideType.SECTION, SlideType.BULLETS, SlideType.CARDS, SlideType.METRICS, SlideType.IMAGE_TEXT} and not self.title:
            raise ValueError(f"slide type '{self.type.value}' requires a title")

        if self.type == SlideType.BULLETS and not (self.body or self.bullets):
            raise ValueError("bullets slide requires body or bullets")

        if self.type == SlideType.BULLETS and len(self.bullets) > MAX_BULLETS_PER_SLIDE:
            raise ValueError(f"bullets slide supports up to {MAX_BULLETS_PER_SLIDE} bullets")

        if self.type == SlideType.CARDS and len(self.cards) != 3:
            raise ValueError("cards slide requires exactly 3 cards")

        if self.type == SlideType.METRICS and not self.metrics:
            raise ValueError("metrics slide requires at least one metric")

        if self.type == SlideType.METRICS and len(self.metrics) > MAX_METRICS_PER_SLIDE:
            raise ValueError(f"metrics slide supports up to {MAX_METRICS_PER_SLIDE} metrics")

        if self.type == SlideType.IMAGE_TEXT and not (self.body or self.bullets):
            raise ValueError("image_text slide requires body or bullets")

        if self.type == SlideType.IMAGE_TEXT and len(self.bullets) > MAX_BULLETS_PER_SLIDE:
            raise ValueError(f"image_text slide supports up to {MAX_BULLETS_PER_SLIDE} bullets")

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
        if not json_path.exists():
            raise FileNotFoundError(f"Input JSON not found: {json_path}")
        return cls.model_validate(json.loads(json_path.read_text(encoding="utf-8")))
