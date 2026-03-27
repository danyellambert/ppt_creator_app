from __future__ import annotations

from ppt_creator.schema import PresentationInput


def _shorten_words(value: str | None, *, max_words: int) -> str | None:
    if not value:
        return value
    words = value.split()
    if len(words) <= max_words:
        return value.strip()
    return " ".join(words[:max_words]).rstrip(" ,;:.!?") + "..."


def _shorten_list(values: list[str], *, max_items: int, max_words: int) -> list[str]:
    return [_shorten_words(value, max_words=max_words) or "" for value in values[:max_items]]


def _refine_columns(columns: list[dict[str, object]]) -> list[dict[str, object]]:
    refined: list[dict[str, object]] = []
    for column in columns[:2]:
        updated = dict(column)
        updated["title"] = _shorten_words(str(column.get("title") or ""), max_words=7) or column.get("title")
        updated["body"] = _shorten_words(column.get("body") if isinstance(column.get("body"), str) else None, max_words=26)
        updated["bullets"] = _shorten_list(
            [str(item) for item in column.get("bullets", []) if isinstance(item, str)],
            max_items=3,
            max_words=10,
        )
        updated["footer"] = _shorten_words(column.get("footer") if isinstance(column.get("footer"), str) else None, max_words=8)
        updated["tag"] = _shorten_words(column.get("tag") if isinstance(column.get("tag"), str) else None, max_words=5)
        refined.append(updated)
    return refined


def _refine_table(slide: dict[str, object]) -> None:
    slide["table_columns"] = _shorten_list(
        [str(item) for item in slide.get("table_columns", []) if isinstance(item, str)],
        max_items=4,
        max_words=4,
    )
    rows = slide.get("table_rows", [])
    if not isinstance(rows, list):
        return
    max_cols = len(slide.get("table_columns", [])) or 4
    slide["table_rows"] = [
        [_shorten_words(str(cell), max_words=5) or "" for cell in row[:max_cols]]
        for row in rows[:6]
        if isinstance(row, list)
    ]


def _refine_cards(items: list[dict[str, object]], *, max_items: int) -> list[dict[str, object]]:
    refined: list[dict[str, object]] = []
    for item in items[:max_items]:
        updated = dict(item)
        updated["title"] = _shorten_words(str(item.get("title") or ""), max_words=8) or item.get("title")
        updated["body"] = _shorten_words(item.get("body") if isinstance(item.get("body"), str) else None, max_words=24)
        if "footer" in updated:
            updated["footer"] = _shorten_words(updated.get("footer") if isinstance(updated.get("footer"), str) else None, max_words=8)
        if "tag" in updated:
            updated["tag"] = _shorten_words(updated.get("tag") if isinstance(updated.get("tag"), str) else None, max_words=5)
        refined.append(updated)
    return refined


def refine_presentation_payload(
    payload: dict[str, object],
    *,
    review: dict[str, object] | None = None,
) -> dict[str, object]:
    updated_payload = {
        "presentation": dict(payload.get("presentation") or {}),
        "slides": [dict(slide) for slide in (payload.get("slides") or []) if isinstance(slide, dict)],
    }
    review_lookup = {
        int(slide_review["slide_number"]): slide_review
        for slide_review in (review or {}).get("slides", [])
    }

    for index, slide in enumerate(updated_payload["slides"], start=1):
        slide_review = review_lookup.get(index, {})
        risk_level = str(slide_review.get("risk_level") or "low")

        if risk_level in {"medium", "high"}:
            slide["title"] = _shorten_words(slide.get("title") if isinstance(slide.get("title"), str) else None, max_words=12)
            slide["subtitle"] = _shorten_words(
                slide.get("subtitle") if isinstance(slide.get("subtitle"), str) else None,
                max_words=18,
            )

        slide_type = str(slide.get("type") or "")
        if slide_type in {"agenda", "bullets", "image_text", "summary"}:
            slide["body"] = _shorten_words(slide.get("body") if isinstance(slide.get("body"), str) else None, max_words=30)
            slide["bullets"] = _shorten_list(
                [str(item) for item in slide.get("bullets", []) if isinstance(item, str)],
                max_items=4,
                max_words=10,
            )

        if slide_type == "cards":
            slide["cards"] = _refine_cards(
                [item for item in slide.get("cards", []) if isinstance(item, dict)],
                max_items=3,
            )

        if slide_type == "metrics":
            metrics = []
            for metric in [item for item in slide.get("metrics", []) if isinstance(item, dict)][:4]:
                updated = dict(metric)
                updated["label"] = _shorten_words(str(metric.get("label") or ""), max_words=5) or metric.get("label")
                updated["detail"] = _shorten_words(metric.get("detail") if isinstance(metric.get("detail"), str) else None, max_words=16)
                updated["trend"] = _shorten_words(metric.get("trend") if isinstance(metric.get("trend"), str) else None, max_words=6)
                metrics.append(updated)
            slide["metrics"] = metrics

        if slide_type == "timeline":
            slide["timeline_items"] = _refine_cards(
                [item for item in slide.get("timeline_items", []) if isinstance(item, dict)],
                max_items=4,
            )

        if slide_type in {"comparison", "two_column"}:
            key = "comparison_columns" if slide_type == "comparison" else "two_column_columns"
            slide[key] = _refine_columns([item for item in slide.get(key, []) if isinstance(item, dict)])

        if slide_type == "table":
            _refine_table(slide)

        if slide_type == "faq":
            slide["faq_items"] = _refine_cards(
                [item for item in slide.get("faq_items", []) if isinstance(item, dict)],
                max_items=3,
            )

        if slide_type == "chart":
            slide["body"] = _shorten_words(slide.get("body") if isinstance(slide.get("body"), str) else None, max_words=24)
            slide["chart_categories"] = [str(item) for item in slide.get("chart_categories", [])[:6] if isinstance(item, str)]
            slide["chart_series"] = [item for item in slide.get("chart_series", [])[:3] if isinstance(item, dict)]

        if slide_type == "closing":
            slide["quote"] = _shorten_words(slide.get("quote") if isinstance(slide.get("quote"), str) else None, max_words=24)

    return updated_payload


def refine_presentation_input(
    spec: PresentationInput,
    *,
    review: dict[str, object] | None = None,
) -> PresentationInput:
    refined_payload = refine_presentation_payload(spec.model_dump(mode="json"), review=review)
    return PresentationInput.model_validate(refined_payload)
