from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    generate_presentation_payload_from_briefing,
    review_presentation_density,
    suggest_image_queries_from_briefing,
    summarize_text_to_executive_bullets,
)
from ppt_creator_ai.providers.base import BriefingGenerationResult, DeckCritiqueResult


def _normalize_process_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


class PPTAgentLocalProvider:
    name = "pptagent_local"
    description = "Runs a local GGUF model such as PPTAgent via llama.cpp / llama-cli."

    def playground_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def models_dir(self) -> Path:
        return self.playground_root() / "models"

    def resolve_model_path(self, model_input: str | None = None) -> Path:
        requested = (model_input or os.environ.get("PPT_CREATOR_AI_GGUF_MODEL") or "PPTAgent").strip()
        candidate = Path(requested)
        if candidate.is_file():
            return candidate.resolve()

        models = sorted(self.models_dir().rglob("*.gguf"))
        if not models:
            raise FileNotFoundError("No local .gguf models were found under models/")

        requested_lower = requested.lower()
        exact = [path for path in models if path.name.lower() == requested_lower]
        if len(exact) == 1:
            return exact[0]
        if len(exact) > 1:
            raise ValueError(f"More than one exact GGUF match found for: {requested}")

        partial = [path for path in models if requested_lower in path.name.lower()]
        if len(partial) == 1:
            return partial[0]
        if len(partial) > 1:
            options = ", ".join(path.name for path in partial)
            raise ValueError(f"More than one GGUF partial match found for '{requested}': {options}")

        raise FileNotFoundError(f"No GGUF model matched: {requested}")

    def resolve_runtime_binary(self) -> str:
        explicit = os.environ.get("PPT_CREATOR_AI_RUNTIME")
        if explicit:
            resolved = shutil.which(explicit)
            if resolved is None:
                raise RuntimeError(f"Requested runtime '{explicit}' was not found in PATH")
            return resolved

        for candidate in ("llama-completion", "llama-cli"):
            resolved = shutil.which(candidate)
            if resolved is not None:
                return resolved

        raise RuntimeError("Neither llama-completion nor llama-cli was found in PATH. Install llama.cpp first.")

    def build_prompt(self, briefing: BriefingInput, *, theme_name: str | None = None) -> str:
        effective_theme = theme_name or briefing.theme
        briefing_payload = briefing.model_dump(mode="json")
        prompt = (
            "You are generating structured JSON for a PowerPoint deck renderer. "
            "Return only valid JSON with top-level keys 'presentation' and 'slides'. "
            "Do not wrap the result in markdown. Do not explain your reasoning. "
            "Use only these slide types: title, section, agenda, bullets, cards, metrics, chart, image_text, timeline, comparison, two_column, table, faq, summary, closing. "
            "Prefer concise executive slides and avoid overly dense content. "
            f"Use theme '{effective_theme}'.\n\n"
            "Structured briefing JSON:\n"
            f"{json.dumps(briefing_payload, ensure_ascii=False, indent=2)}\n\n"
            "Return a single JSON object now."
        )
        return prompt

    def build_revision_prompt(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> str:
        effective_theme = theme_name or briefing.theme
        review_summary = {
            "status": review.get("status"),
            "issue_count": review.get("issue_count"),
            "average_score": review.get("average_score"),
            "overflow_risk_count": review.get("overflow_risk_count"),
            "clipping_risk_count": review.get("clipping_risk_count"),
            "collision_risk_count": review.get("collision_risk_count"),
            "balance_warning_count": review.get("balance_warning_count"),
            "top_risk_slides": review.get("top_risk_slides"),
        }
        prompt = (
            "You are revising an existing presentation JSON after QA review. "
            "Return only valid JSON with top-level keys 'presentation' and 'slides'. "
            "Do not wrap the result in markdown. Do not explain your reasoning. "
            "Keep the output compatible with these slide types: title, section, agenda, bullets, cards, metrics, chart, image_text, timeline, comparison, two_column, table, faq, summary, closing. "
            "Preserve the overall storyline, but tighten dense slides, reduce clipping/collision risk, and improve executive readability. "
            "Rewrite weak titles, subtitles, and summary bullets into sharper executive language when needed. "
            f"Use theme '{effective_theme}'.\n\n"
            "Structured briefing JSON:\n"
            f"{json.dumps(briefing.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            "Current presentation JSON:\n"
            f"{json.dumps(current_payload, ensure_ascii=False, indent=2)}\n\n"
            "QA review summary JSON:\n"
            f"{json.dumps(review_summary, ensure_ascii=False, indent=2)}\n\n"
            "Slide critique guidance JSON:\n"
            f"{json.dumps(slide_critiques[:8], ensure_ascii=False, indent=2)}\n\n"
        )
        if feedback_messages:
            prompt += "Additional revision guidance:\n- " + "\n- ".join(feedback_messages) + "\n\n"
        prompt += "Return a single revised JSON object now."
        return prompt

    def build_critique_prompt(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> str:
        effective_theme = theme_name or briefing.theme
        review_summary = {
            "status": review.get("status"),
            "issue_count": review.get("issue_count"),
            "average_score": review.get("average_score"),
            "overflow_risk_count": review.get("overflow_risk_count"),
            "clipping_risk_count": review.get("clipping_risk_count"),
            "collision_risk_count": review.get("collision_risk_count"),
            "balance_warning_count": review.get("balance_warning_count"),
            "top_risk_slides": review.get("top_risk_slides"),
        }
        prompt = (
            "You are critiquing an existing presentation JSON after QA review. "
            "Return only valid JSON with a top-level key 'slide_critiques'. "
            "Do not wrap the result in markdown. Do not explain your reasoning outside the JSON. "
            "For each risky slide, provide concise slide-by-slide critique that combines briefing intent, QA review, and visual/layout feedback. "
            "Each critique object should contain: slide_number, slide_type, title, risk_level, issues, rewrite_guidance, visual_guidance, executive_tone_guidance. "
            f"Use theme '{effective_theme}' as context.\n\n"
            "Structured briefing JSON:\n"
            f"{json.dumps(briefing.model_dump(mode='json'), ensure_ascii=False, indent=2)}\n\n"
            "Current presentation JSON:\n"
            f"{json.dumps(current_payload, ensure_ascii=False, indent=2)}\n\n"
            "QA review summary JSON:\n"
            f"{json.dumps(review_summary, ensure_ascii=False, indent=2)}\n\n"
            "Existing heuristic slide critiques JSON:\n"
            f"{json.dumps(slide_critiques[:8], ensure_ascii=False, indent=2)}\n\n"
        )
        if feedback_messages:
            prompt += "Additional visual/QA guidance:\n- " + "\n- ".join(feedback_messages) + "\n\n"
        prompt += "Return a single JSON object with the slide critiques now."
        return prompt

    def validate_generated_payload(
        self,
        normalized_payload: dict[str, object],
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        fallback_payload: dict[str, object] | None = None,
    ) -> PresentationInput:
        try:
            return PresentationInput.model_validate(normalized_payload)
        except Exception:
            payload = fallback_payload or generate_presentation_payload_from_briefing(briefing, theme_name=theme_name)
            return PresentationInput.model_validate(payload)

    def build_presentation_meta(
        self,
        presentation_payload: dict[str, object],
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        title_slide_data: dict[str, object] | None = None,
    ) -> dict[str, object]:
        title_data = title_slide_data or {}
        client_name = (
            presentation_payload.get("client_name")
            or title_data.get("client_name")
            or briefing.client_name
        )
        return {
            "title": presentation_payload.get("title") or title_data.get("title") or briefing.title,
            "subtitle": presentation_payload.get("subtitle") or title_data.get("subtitle") or briefing.subtitle,
            "author": presentation_payload.get("author") or title_data.get("author") or briefing.author,
            "date": presentation_payload.get("date") or title_data.get("date") or briefing.date,
            "theme": theme_name or briefing.theme,
            "client_name": client_name,
            "footer_text": presentation_payload.get("footer_text")
            or (f"{client_name} • Briefing deck" if client_name else None),
        }

    def normalize_slide_payload(
        self,
        slide_payload: dict[str, object],
        briefing: BriefingInput,
    ) -> dict[str, object]:
        if "type" in slide_payload and "data" not in slide_payload:
            return dict(slide_payload)

        slide_kind = str(slide_payload.get("slide") or slide_payload.get("type") or "").strip().lower()
        slide_kind = slide_kind.replace("-", "_").replace(" ", "_")
        data = slide_payload.get("data") if isinstance(slide_payload.get("data"), dict) else slide_payload

        content = data.get("content") or data.get("body")
        fallback_bullets = summarize_text_to_executive_bullets(
            content if isinstance(content, str) else None,
            max_bullets=4,
            max_words=10,
        )

        def bullets_slide(title: str | None) -> dict[str, object]:
            return {
                "type": "bullets",
                "title": title or "Key points",
                "body": content if isinstance(content, str) else None,
                "bullets": fallback_bullets,
            }

        if slide_kind == "title":
            return {
                "type": "title",
                "title": data.get("title"),
                "subtitle": data.get("subtitle"),
                "body": data.get("body"),
            }

        if slide_kind == "section":
            title = data.get("section") or data.get("title") or "Section"
            content = data.get("content") or data.get("body")
            if content:
                return {
                    "type": "bullets",
                    "title": title,
                    "body": content,
                }
            return {
                "type": "section",
                "title": title,
                "section_label": "Section",
            }

        if slide_kind == "agenda":
            return {
                "type": "agenda",
                "title": data.get("title") or "Agenda",
                "bullets": data.get("bullets") or data.get("items") or fallback_bullets or briefing.outline[:6],
            }

        if slide_kind == "bullets":
            return {
                "type": "bullets",
                "title": data.get("title") or "Key points",
                "body": content if isinstance(content, str) else None,
                "bullets": data.get("bullets") or fallback_bullets,
            }

        if slide_kind == "cards":
            cards = data.get("cards") or []
            if cards:
                return {
                    "type": "cards",
                    "title": data.get("title") or "Cards",
                    "cards": cards,
                }
            return {
                **bullets_slide(data.get("title") or "Cards"),
            }

        if slide_kind == "metrics":
            metrics = data.get("metrics") or [metric.model_dump(mode="json") for metric in briefing.metrics[:4]]
            if metrics:
                return {
                    "type": "metrics",
                    "title": data.get("title") or "Headline metrics",
                    "metrics": metrics,
                }
            return {
                **bullets_slide(data.get("title") or "Headline metrics"),
            }

        if slide_kind == "chart":
            chart_categories = data.get("chart_categories") or data.get("categories") or []
            chart_series = data.get("chart_series") or data.get("series") or []
            if chart_categories and chart_series:
                return {
                    "type": "chart",
                    "title": data.get("title") or "Chart",
                    "chart_categories": chart_categories,
                    "chart_series": chart_series,
                }
            return {
                **bullets_slide(data.get("title") or "Chart"),
            }

        if slide_kind == "image_text":
            return {
                "type": "image_text",
                "title": data.get("title") or "Image",
                "body": content if isinstance(content, str) else None,
                "bullets": data.get("bullets") or fallback_bullets,
                "image_path": data.get("image_path"),
                "image_caption": data.get("image_caption") or data.get("caption"),
            }

        if slide_kind in {"timeline", "milestones"}:
            raw_items = data.get("timeline_items") or data.get("milestones") or [
                milestone.model_dump(mode="json") for milestone in briefing.milestones[:5]
            ]
            timeline_items = [
                {
                    "title": item.get("title"),
                    "body": item.get("body") or item.get("detail"),
                    "tag": item.get("tag") or item.get("phase"),
                    "footer": item.get("footer"),
                }
                for item in raw_items
                if isinstance(item, dict)
            ]
            if len(timeline_items) < 2:
                return bullets_slide(data.get("title") or "Execution timeline")
            return {
                "type": "timeline",
                "title": data.get("title") or "Execution timeline",
                "timeline_items": timeline_items,
            }

        if slide_kind == "comparison":
            comparison_columns = data.get("comparison_columns") or data.get("columns") or [
                option.model_dump(mode="json") for option in briefing.options[:2]
            ]
            if len(comparison_columns) != 2:
                return bullets_slide(data.get("title") or "Comparison")
            return {
                "type": "comparison",
                "title": data.get("title") or "Comparison",
                "comparison_columns": comparison_columns,
            }

        if slide_kind == "two_column":
            two_column_columns = data.get("two_column_columns") or data.get("columns") or [
                option.model_dump(mode="json") for option in briefing.options[:2]
            ]
            if len(two_column_columns) != 2:
                return bullets_slide(data.get("title") or "Two column")
            return {
                "type": "two_column",
                "title": data.get("title") or "Two column",
                "two_column_columns": two_column_columns,
            }

        if slide_kind == "table":
            table_columns = data.get("table_columns") or data.get("columns") or []
            table_rows = data.get("table_rows") or data.get("rows") or []
            if (not table_columns or not table_rows) and briefing.metrics:
                table_columns = ["Metric", "Value", "Trend"]
                table_rows = [
                    [metric.label, metric.value, metric.trend or ""]
                    for metric in briefing.metrics[:6]
                ]
            if len(table_columns) < 2 or not table_rows:
                return bullets_slide(data.get("title") or "Table")
            return {
                "type": "table",
                "title": data.get("title") or "Table",
                "table_columns": table_columns,
                "table_rows": table_rows,
            }

        if slide_kind in {"faq", "faqs"}:
            raw_items = data.get("faq_items") or data.get("faqs") or [
                {"question": faq.question, "answer": faq.answer}
                for faq in briefing.faqs[:4]
            ]
            faq_items = [
                {
                    "title": item.get("title") or item.get("question"),
                    "body": item.get("body") or item.get("answer"),
                }
                for item in raw_items
                if isinstance(item, dict)
            ]
            if len(faq_items) < 2:
                return bullets_slide(data.get("title") or "Executive FAQ")
            return {
                "type": "faq",
                "title": data.get("title") or "Executive FAQ",
                "faq_items": faq_items,
            }

        if slide_kind == "summary":
            return {
                "type": "summary",
                "title": data.get("title") or "Executive summary",
                "body": data.get("content") or data.get("body"),
                "bullets": data.get("bullets") or [],
            }

        if slide_kind == "closing":
            return {
                "type": "closing",
                "title": data.get("title") or "Closing thought",
                "quote": data.get("closing_quote") or data.get("quote") or data.get("content"),
            }

        raise ValueError(f"Unsupported slide payload from local model: {slide_kind or 'unknown'}")

    def normalize_generated_payload(
        self,
        payload: dict[str, object],
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
    ) -> dict[str, object]:
        if "presentation" in payload and "slides" in payload:
            presentation_payload = payload.get("presentation")
            slides_payload = payload.get("slides")
        elif isinstance(payload.get("presentation"), dict) and isinstance(payload["presentation"].get("slides"), list):
            presentation_payload = payload.get("presentation")
            slides_payload = payload["presentation"].get("slides")
        else:
            raise ValueError("Model output did not contain a recognizable presentation/slides payload")

        presentation_dict = presentation_payload if isinstance(presentation_payload, dict) else {}
        slides_list = slides_payload if isinstance(slides_payload, list) else []
        title_slide_data = next(
            (
                item.get("data")
                for item in slides_list
                if isinstance(item, dict)
                and str(item.get("slide") or item.get("type") or "").strip().lower().replace("-", "_") == "title"
                and isinstance(item.get("data"), dict)
            ),
            None,
        )

        normalized_slides = [
            self.normalize_slide_payload(item, briefing)
            for item in slides_list
            if isinstance(item, dict)
        ]
        if not normalized_slides or normalized_slides[0].get("type") != "title":
            normalized_slides.insert(
                0,
                {
                    "type": "title",
                    "title": briefing.title,
                    "subtitle": briefing.subtitle,
                    "body": briefing.objective,
                },
            )

        return {
            "presentation": self.build_presentation_meta(
                presentation_dict,
                briefing,
                theme_name=theme_name,
                title_slide_data=title_slide_data,
            ),
            "slides": normalized_slides,
        }

    def run_model(self, model_path: Path, prompt: str) -> str:
        runtime_binary = self.resolve_runtime_binary()
        runtime_name = Path(runtime_binary).name

        ctx_size = os.environ.get("PPT_CREATOR_AI_CTX_SIZE", "8192")
        max_tokens = os.environ.get("PPT_CREATOR_AI_MAX_TOKENS", "1800")
        gpu_layers = os.environ.get("PPT_CREATOR_AI_GPU_LAYERS", "-1")
        temperature = os.environ.get("PPT_CREATOR_AI_TEMPERATURE", "0.2")
        timeout_seconds = int(os.environ.get("PPT_CREATOR_AI_TIMEOUT_SECONDS", "180"))
        raw_output_path = os.environ.get("PPT_CREATOR_AI_RAW_OUTPUT_PATH")

        command = [
            runtime_binary,
            "-m",
            str(model_path),
            "-c",
            ctx_size,
            "-ngl",
            gpu_layers,
            "-n",
            max_tokens,
            "--temp",
            temperature,
            "--simple-io",
            "-p",
            prompt,
        ]

        if runtime_name == "llama-completion":
            command.insert(-3, "-no-cnv")
        else:
            command.insert(-3, "--single-turn")
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                stdin=subprocess.DEVNULL,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            partial_stdout = _normalize_process_output(exc.stdout)
            partial_stderr = _normalize_process_output(exc.stderr)
            partial_output = (partial_stdout + (f"\n{partial_stderr}" if partial_stderr else "")).strip()
            if raw_output_path:
                raw_output_file = Path(raw_output_path)
                raw_output_file.parent.mkdir(parents=True, exist_ok=True)
                raw_output_file.write_text(partial_output + "\n", encoding="utf-8")
            raise RuntimeError(
                f"{runtime_name} timed out before finishing. This often means the model is too slow or entered an unexpected mode. "
                f"Increase PPT_CREATOR_AI_TIMEOUT_SECONDS if needed. Partial output: {partial_output[:400]}"
            ) from exc
        output_stdout = _normalize_process_output(completed.stdout)
        output_stderr = _normalize_process_output(completed.stderr)
        output = output_stdout + (f"\n{output_stderr}" if output_stderr else "")
        if raw_output_path:
            raw_output_file = Path(raw_output_path)
            raw_output_file.parent.mkdir(parents=True, exist_ok=True)
            raw_output_file.write_text(output + "\n", encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(f"{runtime_name} failed with exit code {completed.returncode}: {output.strip()}")
        return output

    def extract_json_payload(self, text: str) -> dict[str, object]:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if not isinstance(candidate, dict) or "presentation" not in candidate:
                continue
            if "slides" in candidate:
                return candidate
            presentation_payload = candidate.get("presentation")
            if isinstance(presentation_payload, dict) and "slides" in presentation_payload:
                return candidate
        raise ValueError("Could not extract presentation JSON from model output")

    def extract_slide_critiques_payload(self, text: str) -> list[dict[str, object]]:
        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            critiques = candidate.get("slide_critiques") if isinstance(candidate, dict) else None
            if isinstance(critiques, list):
                return [item for item in critiques if isinstance(item, dict)]
        raise ValueError("Could not extract slide critique JSON from model output")

    def normalize_slide_critiques(
        self,
        critiques: list[dict[str, object]],
        *,
        fallback_slide_critiques: list[dict[str, object]],
        max_critiques: int = 8,
    ) -> list[dict[str, object]]:
        normalized: list[dict[str, object]] = []
        for item in critiques[:max_critiques]:
            slide_number = item.get("slide_number")
            if not isinstance(slide_number, int):
                continue
            normalized.append(
                {
                    "slide_number": slide_number,
                    "slide_type": str(item.get("slide_type") or "slide"),
                    "title": str(item.get("title") or f"Slide {slide_number:02d}"),
                    "risk_level": str(item.get("risk_level") or "medium"),
                    "issues": [str(issue) for issue in (item.get("issues") or []) if str(issue).strip()][:4],
                    "rewrite_guidance": [
                        str(guidance) for guidance in (item.get("rewrite_guidance") or []) if str(guidance).strip()
                    ][:4],
                    "visual_guidance": [
                        str(guidance) for guidance in (item.get("visual_guidance") or []) if str(guidance).strip()
                    ][:4],
                    "executive_tone_guidance": [
                        str(guidance)
                        for guidance in (item.get("executive_tone_guidance") or [])
                        if str(guidance).strip()
                    ][:4],
                }
            )
        return normalized or fallback_slide_critiques[:max_critiques]

    def generate(
        self,
        briefing: BriefingInput,
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        model_path = self.resolve_model_path()
        prompt = self.build_prompt(briefing, theme_name=theme_name)
        if feedback_messages:
            prompt += "\n\nAdditional regeneration guidance:\n- " + "\n- ".join(feedback_messages)
        raw_output = self.run_model(model_path, prompt)
        payload = self.extract_json_payload(raw_output)
        normalized_payload = self.normalize_generated_payload(payload, briefing, theme_name=theme_name)
        spec = self.validate_generated_payload(normalized_payload, briefing, theme_name=theme_name)
        normalized_payload = spec.model_dump(mode="json")

        summary_source = " ".join(
            filter(
                None,
                [briefing.objective, briefing.context, *briefing.key_messages[:3], *briefing.recommendations[:3]],
            )
        )
        analysis = {
            "briefing_title": briefing.title,
            "provider": self.name,
            "model_path": str(model_path),
            "theme": spec.presentation.theme,
            "generated_slide_count": len(spec.slides),
            "feedback_messages": feedback_messages or [],
            "executive_summary_bullets": briefing.recommendations[:3]
            or summarize_text_to_executive_bullets(summary_source, max_bullets=3),
            "image_suggestions": suggest_image_queries_from_briefing(briefing),
            "density_review": review_presentation_density(spec),
        }
        return BriefingGenerationResult(
            provider_name=self.name,
            payload=normalized_payload,
            analysis=analysis,
        )

    def revise_generated_deck(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> BriefingGenerationResult:
        model_path = self.resolve_model_path()
        prompt = self.build_revision_prompt(
            briefing,
            current_payload,
            review,
            slide_critiques,
            theme_name=theme_name,
            feedback_messages=feedback_messages,
        )
        raw_output = self.run_model(model_path, prompt)
        payload = self.extract_json_payload(raw_output)
        normalized_payload = self.normalize_generated_payload(payload, briefing, theme_name=theme_name)
        spec = self.validate_generated_payload(
            normalized_payload,
            briefing,
            theme_name=theme_name,
            fallback_payload=current_payload,
        )
        normalized_payload = spec.model_dump(mode="json")
        analysis = {
            "briefing_title": briefing.title,
            "provider": self.name,
            "model_path": str(model_path),
            "theme": spec.presentation.theme,
            "generated_slide_count": len(spec.slides),
            "feedback_messages": feedback_messages or [],
            "revision_mode": "llm_review",
            "source_issue_count": review.get("issue_count"),
            "slide_critique_count": len(slide_critiques),
            "density_review": review_presentation_density(spec),
        }
        return BriefingGenerationResult(
            provider_name=self.name,
            payload=normalized_payload,
            analysis=analysis,
        )

    def critique_generated_deck(
        self,
        briefing: BriefingInput,
        current_payload: dict[str, object],
        review: dict[str, object],
        slide_critiques: list[dict[str, object]],
        *,
        theme_name: str | None = None,
        feedback_messages: list[str] | None = None,
    ) -> DeckCritiqueResult:
        model_path = self.resolve_model_path()
        fallback_used = False
        try:
            raw_output = self.run_model(
                model_path,
                self.build_critique_prompt(
                    briefing,
                    current_payload,
                    review,
                    slide_critiques,
                    theme_name=theme_name,
                    feedback_messages=feedback_messages,
                ),
            )
            critiques = self.normalize_slide_critiques(
                self.extract_slide_critiques_payload(raw_output),
                fallback_slide_critiques=slide_critiques,
            )
        except Exception:
            critiques = slide_critiques
            fallback_used = True

        return DeckCritiqueResult(
            provider_name=self.name,
            critiques=critiques,
            analysis={
                "provider": self.name,
                "model_path": str(model_path),
                "critique_mode": "llm_slide_critique",
                "feedback_messages": feedback_messages or [],
                "fallback_used": fallback_used,
                "critique_count": len(critiques),
            },
        )
