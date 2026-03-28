from __future__ import annotations

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


def test_provider_registry_exposes_heuristic_provider() -> None:
    assert list_provider_names() == ["anthropic", "heuristic", "ollama", "openai", "pptagent_local"]
    provider = get_provider("heuristic")
    assert provider.name == "heuristic"


def test_provider_registry_exposes_anthropic_provider() -> None:
    provider = get_provider("anthropic")
    assert provider.name == "anthropic"


def test_provider_registry_exposes_ollama_provider() -> None:
    provider = get_provider("ollama")
    assert provider.name == "ollama"


def test_provider_registry_exposes_openai_provider() -> None:
    provider = get_provider("openai")
    assert provider.name == "openai"


def test_provider_registry_exposes_local_pptagent_provider() -> None:
    provider = get_provider("pptagent_local")
    assert provider.name == "pptagent_local"
