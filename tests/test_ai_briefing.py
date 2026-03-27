from __future__ import annotations

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    build_briefing_analysis,
    generate_presentation_input_from_briefing,
    generate_presentation_payload_from_briefing,
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
    assert analysis["density_review"]["status"] in {"ok", "review"}


def test_provider_registry_exposes_heuristic_provider() -> None:
    assert list_provider_names() == ["heuristic"]
    provider = get_provider("heuristic")
    assert provider.name == "heuristic"
