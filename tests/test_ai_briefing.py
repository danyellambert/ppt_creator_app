from __future__ import annotations

import json
from urllib import error

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    build_briefing_analysis,
    derive_briefing_freeform_signals,
    generate_presentation_input_from_briefing,
    generate_presentation_payload_from_briefing,
    suggest_slide_image_queries_from_briefing,
    summarize_text_to_executive_bullets,
)
from ppt_creator_ai.providers import get_provider, list_provider_names


def test_briefing_example_generates_valid_presentation_payload() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    payload = generate_presentation_payload_from_briefing(briefing)
    spec = PresentationInput.model_validate(payload)

    assert spec.presentation.title == briefing.title
    assert len(spec.slides) >= 6
    assert spec.slides[0].type.value == "title"
    assert any(slide.type.value == "agenda" for slide in spec.slides)
    assert any(slide.type.value == "summary" for slide in spec.slides)


def test_briefing_generation_returns_presentation_input() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    spec = generate_presentation_input_from_briefing(briefing)

    assert isinstance(spec, PresentationInput)
    assert spec.presentation.client_name == "Acme Revenue Team"


def test_text_summarizer_builds_compact_executive_bullets() -> None:
    bullets = summarize_text_to_executive_bullets(
        "Teams are overloaded with repetitive work. Managers need better visibility into execution quality. The pilot should stay narrow before scaling.",
        max_bullets=3,
        max_words=8,
    )

    assert len(bullets) == 3
    assert bullets[0].startswith("Teams are overloaded")


def test_briefing_analysis_provides_image_suggestions_and_density_review() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    analysis = build_briefing_analysis(briefing)

    assert analysis["executive_summary_bullets"]
    assert analysis["image_suggestions"]
    assert analysis["slide_image_suggestions"]
    assert analysis["density_review"]["status"] in {"ok", "review"}


def test_slide_image_suggestions_are_granular_by_slide_type() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    suggestions = suggest_slide_image_queries_from_briefing(briefing)

    slide_types = {item["slide_type"] for item in suggestions}
    assert "title" in slide_types
    assert "metrics" in slide_types
    assert "timeline" in slide_types
    assert any(item["queries"] for item in suggestions)


def test_slide_image_suggestions_include_asset_style_and_focal_point_hints() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    suggestions = suggest_slide_image_queries_from_briefing(briefing)

    assert suggestions
    for item in suggestions:
        assert item["asset_style"]
        assert item["composition_notes"]
        assert 0.0 <= item["focal_point"]["x"] <= 1.0
        assert 0.0 <= item["focal_point"]["y"] <= 1.0

    title_hint = next(item for item in suggestions if item["slide_type"] == "title")
    assert title_hint["focal_point"]["y"] < 0.5


def test_briefing_freeform_text_derives_content_signals() -> None:
    briefing = BriefingInput.model_validate(
        {
            "title": "AI copilots for sales teams",
            "briefing_text": (
                "Sales leaders are overloaded with repetitive preparation work and inconsistent storytelling. "
                "We should start with one workflow for leadership meeting prep, measure time saved and quality lift, and only then expand scope. "
                "The rollout should stay narrow in the first month and follow a milestone-based plan."
            ),
        }
    )

    derived = derive_briefing_freeform_signals(briefing)

    assert derived["objective"]
    assert derived["context"]
    assert derived["key_messages"]
    assert derived["recommendations"]
    assert derived["outline"]


def test_briefing_freeform_text_can_generate_valid_presentation() -> None:
    briefing = BriefingInput.model_validate(
        {
            "title": "AI copilots for sales teams",
            "briefing_text": (
                "Sales leaders are overloaded with repetitive preparation work and inconsistent storytelling. "
                "We should start with one workflow for leadership meeting prep, measure time saved and quality lift, and only then expand scope."
            ),
        }
    )

    spec = generate_presentation_input_from_briefing(briefing)

    assert isinstance(spec, PresentationInput)
    assert len(spec.slides) >= 4
    assert any(slide.type.value == "agenda" for slide in spec.slides)
    assert any(slide.type.value == "summary" for slide in spec.slides)


def test_provider_registry_exposes_heuristic_and_local_service() -> None:
    assert list_provider_names() == ["heuristic", "local_service"]
    assert get_provider("heuristic").name == "heuristic"
    assert get_provider("local_service").name == "local_service"
    assert get_provider("service").name == "local_service"
    assert get_provider("hf_local_llm_service").name == "local_service"


def test_local_service_provider_surfaces_connection_error(monkeypatch) -> None:
    provider = get_provider("local_service")

    def _url_error(*args, **kwargs):
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _url_error)

    try:
        provider.generate(BriefingInput.from_path("examples/briefing_sales.json"))
    except RuntimeError as exc:
        assert "hf_local_llm_service" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when hf_local_llm_service is unreachable")


def test_local_service_provider_normalizes_mocked_payload(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    response_payload = {
        "provider_name": "ollama",
        "payload": {
            "presentation": {
                "title": "AI copilots for sales teams",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {"type": "title", "title": "AI copilots for sales teams"},
                {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
                {"type": "closing", "title": "Closing", "quote": "Done."},
            ],
        },
        "analysis": {"provider": "ollama"},
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response())

    result = provider.generate(briefing)

    spec = PresentationInput.model_validate(result.payload)
    assert result.provider_name == "ollama"
    assert spec.presentation.title == "AI copilots for sales teams"
