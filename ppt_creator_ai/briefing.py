from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ppt_creator.schema import PresentationInput


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


class BriefingMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    detail: str | None = None
    trend: str | None = None

    @field_validator("label", "value", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)

    @field_validator("detail", "trend", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class BriefingMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    detail: str | None = None
    phase: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("detail", "phase", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class BriefingOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str | None = None
    bullets: list[str] = Field(default_factory=list)
    footer: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("body", "footer", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("bullets")
    @classmethod
    def clean_bullets(cls, bullets: list[str]) -> list[str]:
        return _clean_string_list(bullets, field_name="option bullet")

    @model_validator(mode="after")
    def validate_has_content(self) -> "BriefingOption":
        if not (self.body or self.bullets):
            raise ValueError("briefing option requires body or bullets")
        return self


class BriefingFAQ(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str

    @field_validator("question", "answer", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)


class BriefingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str | None = None
    audience: str | None = None
    objective: str | None = None
    context: str | None = None
    client_name: str | None = None
    author: str | None = None
    date: str | None = None
    theme: str = "executive_premium_minimal"
    outline: list[str] = Field(default_factory=list)
    key_messages: list[str] = Field(default_factory=list)
    metrics: list[BriefingMetric] = Field(default_factory=list)
    milestones: list[BriefingMilestone] = Field(default_factory=list)
    options: list[BriefingOption] = Field(default_factory=list)
    faqs: list[BriefingFAQ] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    closing_quote: str | None = None

    @field_validator(
        "title",
        mode="before",
    )
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator(
        "subtitle",
        "audience",
        "objective",
        "context",
        "client_name",
        "author",
        "date",
        "closing_quote",
        mode="before",
    )
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("outline", "key_messages", "recommendations")
    @classmethod
    def clean_string_lists(cls, values: list[str], info) -> list[str]:
        return _clean_string_list(values, field_name=info.field_name)

    @field_validator("theme", mode="before")
    @classmethod
    def normalize_theme(cls, value: object) -> str | object:
        if value is None:
            return "executive_premium_minimal"
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized or "executive_premium_minimal"

    @model_validator(mode="after")
    def validate_minimum_signal(self) -> "BriefingInput":
        if not any(
            [
                self.objective,
                self.context,
                self.key_messages,
                self.metrics,
                self.milestones,
                self.options,
                self.faqs,
                self.recommendations,
                self.outline,
            ]
        ):
            raise ValueError("briefing requires at least one content signal beyond the title")
        return self

    @classmethod
    def from_path(cls, path: str | Path) -> "BriefingInput":
        json_path = Path(path)
        if not json_path.exists():
            raise FileNotFoundError(f"Briefing JSON not found: {json_path}")
        return cls.model_validate(json.loads(json_path.read_text(encoding="utf-8")))


def _infer_agenda(briefing: BriefingInput) -> list[str]:
    if briefing.outline:
        return briefing.outline[:6]

    agenda: list[str] = []
    if briefing.objective or briefing.context or briefing.key_messages:
        agenda.append("Situation overview")
    if briefing.metrics:
        agenda.append("Performance signals")
    if briefing.milestones:
        agenda.append("Execution timeline")
    if len(briefing.options) == 2:
        agenda.append("Option framing")
    if len(briefing.faqs) >= 2:
        agenda.append("Executive FAQ")
    agenda.append("Recommendation")
    return agenda[:6]


def generate_presentation_payload_from_briefing(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
) -> dict[str, object]:
    effective_theme = theme_name or briefing.theme
    slides: list[dict[str, object]] = [
        {
            "type": "title",
            "title": briefing.title,
            "subtitle": briefing.subtitle,
            "eyebrow": briefing.audience or "Briefing-generated deck",
            "layout_variant": "hero_cover",
            "body": briefing.objective,
        }
    ]

    agenda = _infer_agenda(briefing)
    if agenda:
        slides.append(
            {
                "type": "agenda",
                "title": "Agenda",
                "subtitle": "Generated from structured briefing",
                "bullets": agenda,
            }
        )

    context_bullets = briefing.key_messages[:6]
    if briefing.objective or briefing.context or context_bullets:
        slides.append(
            {
                "type": "bullets",
                "title": "Situation overview",
                "subtitle": briefing.subtitle,
                "eyebrow": "Context",
                "body": briefing.objective or briefing.context,
                "bullets": context_bullets,
            }
        )

    if briefing.metrics:
        slides.append(
            {
                "type": "metrics",
                "title": "Headline metrics",
                "subtitle": "Signals extracted from the briefing",
                "metrics": [metric.model_dump(mode="json") for metric in briefing.metrics[:4]],
            }
        )

    if len(briefing.milestones) >= 2:
        slides.append(
            {
                "type": "timeline",
                "title": "Execution timeline",
                "subtitle": "Milestones inferred from the briefing",
                "timeline_items": [
                    {
                        "title": milestone.title,
                        "body": milestone.detail,
                        "tag": milestone.phase,
                    }
                    for milestone in briefing.milestones[:5]
                ],
            }
        )

    if len(briefing.options) == 2:
        slides.append(
            {
                "type": "comparison",
                "title": "Option framing",
                "subtitle": "Two-sided decision view built from the briefing",
                "comparison_columns": [option.model_dump(mode="json") for option in briefing.options],
            }
        )

    if len(briefing.faqs) >= 2:
        slides.append(
            {
                "type": "faq",
                "title": "Executive FAQ",
                "faq_items": [
                    {"title": faq.question, "body": faq.answer}
                    for faq in briefing.faqs[:4]
                ],
            }
        )

    summary_bullets = (briefing.recommendations or briefing.key_messages)[:6]
    if summary_bullets or briefing.context:
        slides.append(
            {
                "type": "summary",
                "title": "Executive summary",
                "body": briefing.context,
                "bullets": summary_bullets,
            }
        )

    slides.append(
        {
            "type": "closing",
            "title": "Closing thought",
            "quote": briefing.closing_quote
            or "A structured briefing becomes far more useful when it is translated into a clear decision narrative.",
        }
    )

    return {
        "presentation": {
            "title": briefing.title,
            "subtitle": briefing.subtitle,
            "author": briefing.author,
            "date": briefing.date,
            "theme": effective_theme,
            "client_name": briefing.client_name,
            "footer_text": f"{briefing.client_name} • Briefing deck" if briefing.client_name else None,
        },
        "slides": slides,
    }


def generate_presentation_input_from_briefing(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
) -> PresentationInput:
    payload = generate_presentation_payload_from_briefing(briefing, theme_name=theme_name)
    return PresentationInput.model_validate(payload)
