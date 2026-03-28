from __future__ import annotations

import json
import re
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


def summarize_text_to_executive_bullets(
    text: str | None,
    *,
    max_bullets: int = 3,
    max_words: int = 14,
) -> list[str]:
    if not text:
        return []

    segments = [segment.strip() for segment in re.split(r"[\n\.\?!;]+", text) if segment.strip()]
    bullets: list[str] = []
    for segment in segments:
        words = segment.split()
        shortened = " ".join(words[:max_words]).strip()
        if len(words) > max_words:
            shortened += "..."
        if shortened and shortened not in bullets:
            bullets.append(shortened)
        if len(bullets) >= max_bullets:
            break
    return bullets


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


def suggest_image_queries_from_briefing(
    briefing: BriefingInput,
    *,
    max_suggestions: int = 4,
) -> list[str]:
    suggestions: list[str] = []

    def add_suggestion(value: str | None) -> None:
        if not value:
            return
        cleaned = value.strip()
        if cleaned and cleaned not in suggestions:
            suggestions.append(cleaned)

    add_suggestion(f"{briefing.title} executive presentation background")

    title_lower = briefing.title.lower()
    if "sales" in title_lower or "revenue" in title_lower:
        add_suggestion("sales leadership dashboard and pipeline review")
    if "product" in title_lower:
        add_suggestion("product strategy roadmap workshop")
    if "strategy" in title_lower:
        add_suggestion("executive strategy offsite discussion")

    if briefing.metrics:
        add_suggestion("executive KPI dashboard with growth trend lines")
    if briefing.milestones:
        add_suggestion("program roadmap timeline and milestone workshop")
    if len(briefing.options) == 2:
        add_suggestion("decision workshop with comparison whiteboard")
    if briefing.audience:
        add_suggestion(f"{briefing.audience} leadership meeting")

    return suggestions[:max_suggestions]


def suggest_slide_image_queries_from_briefing(
    briefing: BriefingInput,
    *,
    max_queries_per_slide: int = 3,
) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []

    def _queries(*values: str | None) -> list[str]:
        deduped: list[str] = []
        for value in values:
            if not value:
                continue
            cleaned = value.strip()
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped[:max_queries_per_slide]

    title_context = briefing.title.lower()
    audience_context = briefing.audience or "executive leadership team"

    suggestions.append(
        {
            "slide_key": "title",
            "slide_type": "title",
            "title": briefing.title,
            "queries": _queries(
                f"{briefing.title} executive presentation cover image",
                f"{audience_context} strategy meeting hero background",
            ),
        }
    )

    if briefing.objective or briefing.context or briefing.key_messages:
        suggestions.append(
            {
                "slide_key": "situation_overview",
                "slide_type": "bullets",
                "title": "Situation overview",
                "queries": _queries(
                    f"{briefing.title} business context workshop",
                    f"{audience_context} planning session",
                    "executive team discussion around business priorities",
                ),
            }
        )

    if briefing.metrics:
        metric_labels = ", ".join(metric.label for metric in briefing.metrics[:2])
        suggestions.append(
            {
                "slide_key": "headline_metrics",
                "slide_type": "metrics",
                "title": "Headline metrics",
                "queries": _queries(
                    f"executive KPI dashboard for {briefing.title}",
                    f"business performance dashboard showing {metric_labels}" if metric_labels else None,
                    "leadership dashboard with clean charts and metric cards",
                ),
            }
        )

    if briefing.milestones:
        milestone_titles = ", ".join(item.title for item in briefing.milestones[:3])
        suggestions.append(
            {
                "slide_key": "execution_timeline",
                "slide_type": "timeline",
                "title": "Execution timeline",
                "queries": _queries(
                    f"program roadmap timeline for {briefing.title}",
                    f"milestone planning workshop covering {milestone_titles}" if milestone_titles else None,
                    "strategy roadmap with milestone planning board",
                ),
            }
        )

    if len(briefing.options) == 2:
        left, right = briefing.options
        suggestions.append(
            {
                "slide_key": "option_framing",
                "slide_type": "comparison",
                "title": "Option framing",
                "queries": _queries(
                    f"executive decision workshop comparing {left.title} and {right.title}",
                    "comparison whiteboard for strategic options",
                    f"leadership team evaluating {briefing.title} scenarios",
                ),
            }
        )

    if len(briefing.faqs) >= 2:
        first_question = briefing.faqs[0].question
        suggestions.append(
            {
                "slide_key": "executive_faq",
                "slide_type": "faq",
                "title": "Executive FAQ",
                "queries": _queries(
                    f"executive Q&A session about {briefing.title}",
                    f"leadership meeting addressing question: {first_question}",
                    "boardroom discussion handling objections and decisions",
                ),
            }
        )

    if briefing.recommendations or briefing.key_messages:
        suggestions.append(
            {
                "slide_key": "executive_summary",
                "slide_type": "summary",
                "title": "Executive summary",
                "queries": _queries(
                    f"executive summary visual for {briefing.title}",
                    "leadership alignment and decision summary",
                    "final recommendation slide background for executive meeting",
                ),
            }
        )

    if "sales" in title_context or "revenue" in title_context:
        for suggestion in suggestions:
            if suggestion["slide_key"] == "headline_metrics":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "sales pipeline dashboard and revenue forecast review",
                )
            if suggestion["slide_key"] == "situation_overview":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "sales leadership meeting discussing pipeline and enablement",
                )
    elif "product" in title_context:
        for suggestion in suggestions:
            if suggestion["slide_key"] == "execution_timeline":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "product roadmap planning session with milestones",
                )
            if suggestion["slide_key"] == "situation_overview":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "product strategy workshop with leadership team",
                )

    return suggestions


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


def review_presentation_density(spec: PresentationInput) -> dict[str, object]:
    warnings: list[str] = []
    slide_reviews: list[dict[str, object]] = []

    for index, slide in enumerate(spec.slides, start=1):
        issues: list[str] = []
        body_len = len(slide.body or "")

        if slide.type.value in {"agenda", "bullets", "summary", "image_text"}:
            if len(slide.bullets) > 5:
                issues.append("too many bullets for an executive slide")
            if body_len > 260:
                issues.append("body text is likely too dense")

        if slide.type.value == "timeline" and len(slide.timeline_items) > 4:
            issues.append("timeline may be visually dense")

        if slide.type.value in {"comparison", "two_column"}:
            columns = slide.comparison_columns or slide.two_column_columns
            for column in columns:
                if len(column.bullets) > 3:
                    issues.append(f"column '{column.title}' has too many bullets")

        if slide.type.value == "table":
            if len(slide.table_rows) > 6:
                issues.append("table has many rows for a single slide")
            if len(slide.table_columns) > 4:
                issues.append("table has many columns for executive readability")

        if slide.type.value == "faq" and len(slide.faq_items) > 3:
            issues.append("faq may be too crowded")

        if slide.type.value == "chart" and len(slide.chart_categories) > 6:
            issues.append("chart has many categories for a clean executive view")

        slide_reviews.append(
            {
                "slide_number": index,
                "slide_type": slide.type.value,
                "title": slide.title or slide.type.value,
                "issues": issues,
            }
        )
        for issue in issues:
            warnings.append(f"slide {index:02d} ({slide.title or slide.type.value}): {issue}")

    return {
        "status": "review" if warnings else "ok",
        "warning_count": len(warnings),
        "warnings": warnings,
        "slides": slide_reviews,
    }


def build_generation_feedback_from_review(
    review: dict[str, object],
    *,
    max_messages: int = 8,
) -> list[str]:
    messages: list[str] = []

    def add(message: str) -> None:
        normalized = message.strip()
        if normalized and normalized not in messages and len(messages) < max_messages:
            messages.append(normalized)

    if int(review.get("overflow_risk_count") or 0) > 0:
        add("Reduce slide density overall; prefer fewer bullets, shorter bodies, and more whitespace.")
    if int(review.get("clipping_risk_count") or 0) > 0:
        add("Keep content farther from slide edges and avoid long lines that may clip in the final layout.")
    if int(review.get("balance_warning_count") or 0) > 0:
        add("Balance content more evenly across panels and columns so no region looks overloaded.")

    for slide_review in review.get("top_risk_slides", []) or []:
        if not isinstance(slide_review, dict):
            continue
        slide_number = slide_review.get("slide_number")
        slide_type = str(slide_review.get("slide_type") or "slide")
        title = str(slide_review.get("title") or slide_type)
        if slide_type in {"agenda", "bullets", "summary", "image_text"}:
            add(f"Slide {slide_number} '{title}' should use at most 4 concise bullets and a shorter narrative body.")
        elif slide_type in {"comparison", "two_column"}:
            add(f"Slide {slide_number} '{title}' should distribute content more evenly across both columns and reduce per-column bullets.")
        elif slide_type == "timeline":
            add(f"Slide {slide_number} '{title}' should use fewer timeline items or shorter milestone text.")
        elif slide_type == "table":
            add(f"Slide {slide_number} '{title}' should reduce table rows/columns and simplify cell text.")
        elif slide_type == "faq":
            add(f"Slide {slide_number} '{title}' should keep fewer FAQ items with shorter answers.")
        else:
            add(f"Slide {slide_number} '{title}' should be rewritten with a tighter executive narrative and less dense content.")

        if len(messages) >= max_messages:
            break

    for slide_review in review.get("slides", []) or []:
        if len(messages) >= max_messages:
            break
        if not isinstance(slide_review, dict):
            continue
        issues = slide_review.get("issues") or []
        if not issues:
            continue
        title = str(slide_review.get("title") or slide_review.get("slide_type") or "slide")
        add(f"Address QA issues on '{title}': {'; '.join(str(issue) for issue in issues[:2])}.")

    return messages


def build_slide_critiques_from_review(
    spec: PresentationInput,
    review: dict[str, object],
    *,
    max_critiques: int = 8,
) -> list[dict[str, object]]:
    critiques: list[dict[str, object]] = []
    slide_lookup = {index: slide for index, slide in enumerate(spec.slides, start=1)}

    def _guidance_for_slide(slide_type: str, slide_title: str, issues: list[str]) -> list[str]:
        guidance: list[str] = []
        if slide_type in {"agenda", "bullets", "summary", "image_text"}:
            guidance.append("Keep at most 4 bullets and shorten each line to an executive takeaway.")
            guidance.append("Reduce narrative text so the core message is readable in a few seconds.")
        elif slide_type in {"comparison", "two_column"}:
            guidance.append("Balance both columns and reduce text asymmetry between left and right panels.")
            guidance.append("Prefer fewer bullets per column with sharper contrast between options.")
        elif slide_type == "timeline":
            guidance.append("Use fewer milestones or shorter milestone descriptions.")
        elif slide_type == "table":
            guidance.append("Reduce rows/columns and simplify cell text to key facts only.")
        elif slide_type == "faq":
            guidance.append("Keep fewer FAQ entries and shorten each answer to the essential decision point.")
        elif slide_type == "metrics":
            guidance.append("Trim supporting detail so each KPI remains visually dominant.")
        else:
            guidance.append("Tighten the narrative so the slide reads as an executive summary, not a draft note page.")

        for issue in issues[:2]:
            guidance.append(f"Address this review issue explicitly: {issue}.")
        return guidance[:4]

    for slide_review in review.get("slides", []) or []:
        if len(critiques) >= max_critiques:
            break
        if not isinstance(slide_review, dict):
            continue
        issues = [str(issue) for issue in (slide_review.get("issues") or [])]
        if not issues:
            continue
        slide_number = int(slide_review.get("slide_number") or 0)
        slide = slide_lookup.get(slide_number)
        slide_type = str(slide_review.get("slide_type") or (slide.type.value if slide else "slide"))
        title = str(slide_review.get("title") or (slide.title if slide else slide_type) or slide_type)
        likely_regions = [str(region) for region in (slide_review.get("likely_overflow_regions") or [])]
        critiques.append(
            {
                "slide_number": slide_number,
                "slide_type": slide_type,
                "title": title,
                "risk_level": slide_review.get("risk_level") or "low",
                "issues": issues,
                "likely_overflow_regions": likely_regions,
                "rewrite_guidance": _guidance_for_slide(slide_type, title, issues),
            }
        )

    return critiques


def build_briefing_analysis(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
    feedback_messages: list[str] | None = None,
) -> dict[str, object]:
    spec = generate_presentation_input_from_briefing(
        briefing,
        theme_name=theme_name,
        feedback_messages=feedback_messages,
    )
    summary_source = " ".join(
        filter(
            None,
            [
                briefing.objective,
                briefing.context,
                *briefing.key_messages[:3],
                *briefing.recommendations[:3],
            ],
        )
    )

    return {
        "briefing_title": briefing.title,
        "theme": spec.presentation.theme,
        "generated_slide_count": len(spec.slides),
        "feedback_messages": feedback_messages or [],
        "executive_summary_bullets": briefing.recommendations[:3]
        or summarize_text_to_executive_bullets(summary_source, max_bullets=3),
        "image_suggestions": suggest_image_queries_from_briefing(briefing),
        "slide_image_suggestions": suggest_slide_image_queries_from_briefing(briefing),
        "density_review": review_presentation_density(spec),
    }


def generate_presentation_payload_from_briefing(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
    feedback_messages: list[str] | None = None,
) -> dict[str, object]:
    effective_theme = theme_name or briefing.theme
    compact_mode = bool(feedback_messages)
    derived_context_bullets = summarize_text_to_executive_bullets(
        " ".join(filter(None, [briefing.objective, briefing.context])),
        max_bullets=3 if compact_mode else 4,
    )
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

    agenda = _infer_agenda(briefing)[: 4 if compact_mode else 6]
    if agenda:
        slides.append(
            {
                "type": "agenda",
                "title": "Agenda",
                "subtitle": "Generated from structured briefing",
                "bullets": agenda,
            }
        )

    context_bullets = (briefing.key_messages[: (4 if compact_mode else 6)] or derived_context_bullets[: (4 if compact_mode else 6)])
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
                "metrics": [metric.model_dump(mode="json") for metric in briefing.metrics[: (3 if compact_mode else 4)]],
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
                    for milestone in briefing.milestones[: (4 if compact_mode else 5)]
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
                    for faq in briefing.faqs[: (3 if compact_mode else 4)]
                ],
            }
        )

    summary_bullets = (briefing.recommendations or briefing.key_messages or derived_context_bullets)[: (4 if compact_mode else 6)]
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
    feedback_messages: list[str] | None = None,
) -> PresentationInput:
    payload = generate_presentation_payload_from_briefing(
        briefing,
        theme_name=theme_name,
        feedback_messages=feedback_messages,
    )
    return PresentationInput.model_validate(payload)
