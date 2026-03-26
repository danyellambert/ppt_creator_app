from __future__ import annotations

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    generate_presentation_input_from_briefing,
    generate_presentation_payload_from_briefing,
)


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
