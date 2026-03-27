from __future__ import annotations

import json
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


def test_ai_cli_lists_available_providers(tmp_path: Path, capsys) -> None:
    report = tmp_path / "providers.json"
    result = main(["providers", "--report-json", str(report)])
    captured = capsys.readouterr()

    assert result == 0
    assert report.exists()
    assert "Available providers" in captured.out

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["providers"][0]["name"] == "heuristic"


def test_ai_cli_can_write_analysis_report(tmp_path: Path) -> None:
    output = tmp_path / "generated_deck.json"
    analysis = tmp_path / "briefing_analysis.json"
    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--analysis-json",
            str(analysis),
        ]
    )

    assert result == 0
    assert analysis.exists()

    payload = json.loads(analysis.read_text(encoding="utf-8"))
    assert payload["image_suggestions"]
    assert payload["density_review"]["status"] in {"ok", "review"}
