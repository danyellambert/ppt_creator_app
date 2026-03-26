from __future__ import annotations

import json
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_BULLETS_PER_SLIDE = 6
MAX_METRICS_PER_SLIDE = 4
MAX_TIMELINE_ITEMS = 5

LAYOUT_VARIANTS_BY_SLIDE_TYPE: dict["SlideType", set[str]] = {}


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


def _clean_string_list(values: list[str], *, field_name: str) -> list[str]:
    cleaned: list[str] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, str):
            raise ValueError(f"{field_name} #{index} must be a string")

        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} #{index} cannot be empty")
        cleaned.append(normalized)
    return cleaned


class SlideType(str, Enum):
    TITLE = "title"
    SECTION = "section"
    BULLETS = "bullets"
    CARDS = "cards"
    METRICS = "metrics"
    IMAGE_TEXT = "image_text"
    TIMELINE = "timeline"
    COMPARISON = "comparison"
    CLOSING = "closing"


LAYOUT_VARIANTS_BY_SLIDE_TYPE = {
    SlideType.BULLETS: {"insight_panel", "full_width"},
    SlideType.METRICS: {"standard", "compact"},
    SlideType.IMAGE_TEXT: {"image_right", "image_left"},
}


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


class TimelineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str | None = None
    tag: str | None = None
    footer: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("body", "tag", "footer", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class ComparisonColumn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str | None = None
    bullets: list[str] = Field(default_factory=list)
    footer: str | None = None
    tag: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("body", "footer", "tag", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("bullets")
    @classmethod
    def clean_bullets(cls, bullets: list[str]) -> list[str]:
        return _clean_string_list(bullets, field_name="comparison bullet")

    @model_validator(mode="after")
    def validate_content(self) -> "ComparisonColumn":
        if not (self.body or self.bullets):
            raise ValueError("comparison column requires body or bullets")
        return self


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
    timeline_items: list[TimelineItem] = Field(default_factory=list)
    comparison_columns: list[ComparisonColumn] = Field(default_factory=list)
    quote: str | None = None
    attribution: str | None = None
    section_label: str | None = None
    image_path: str | None = None
    image_caption: str | None = None
    speaker_notes: str | None = None
    layout_variant: str | None = None

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

    @field_validator("layout_variant", mode="before")
    @classmethod
    def normalize_layout_variant(cls, value: object) -> str | None | object:
        if value is None:
            return None
        if not isinstance(value, str):
            return value

        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized or None

    @field_validator("bullets")
    @classmethod
    def clean_bullets(cls, bullets: list[str]) -> list[str]:
        return _clean_string_list(bullets, field_name="bullet")

    @model_validator(mode="after")
    def validate_by_type(self) -> "Slide":
        if self.type in {
            SlideType.TITLE,
            SlideType.SECTION,
            SlideType.BULLETS,
            SlideType.CARDS,
            SlideType.METRICS,
            SlideType.IMAGE_TEXT,
            SlideType.TIMELINE,
            SlideType.COMPARISON,
        } and not self.title:
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

        if self.type == SlideType.TIMELINE and len(self.timeline_items) < 2:
            raise ValueError("timeline slide requires at least 2 timeline_items")

        if self.type == SlideType.TIMELINE and len(self.timeline_items) > MAX_TIMELINE_ITEMS:
            raise ValueError(
                f"timeline slide supports up to {MAX_TIMELINE_ITEMS} timeline_items"
            )

        if self.type == SlideType.COMPARISON and len(self.comparison_columns) != 2:
            raise ValueError("comparison slide requires exactly 2 comparison_columns")

        if self.type == SlideType.CLOSING and not (self.quote or self.title):
            raise ValueError("closing slide requires quote or title")

        if self.layout_variant:
            allowed_variants = LAYOUT_VARIANTS_BY_SLIDE_TYPE.get(self.type)
            if not allowed_variants:
                raise ValueError(f"slide type '{self.type.value}' does not support layout_variant")
            if self.layout_variant not in allowed_variants:
                allowed = ", ".join(sorted(allowed_variants))
                raise ValueError(
                    f"slide type '{self.type.value}' only supports layout_variant values: {allowed}"
                )

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
