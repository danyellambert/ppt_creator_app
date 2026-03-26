from __future__ import annotations

from pathlib import Path

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.cli import main


def test_ai_cli_generates_deck_json_from_briefing(tmp_path: Path) -> None:
    output = tmp_path / "generated_deck.json"
    result = main(["generate", "examples/briefing_sales.json", str(output)])

    assert result == 0
    assert output.exists()

    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "AI copilots for sales teams"
    assert len(spec.slides) >= 6
