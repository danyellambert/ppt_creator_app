from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.cli import main
from ppt_creator_ai.providers import get_provider
from ppt_creator_ai.providers.base import BriefingGenerationResult


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
    provider_names = [provider["name"] for provider in payload["providers"]]
    assert provider_names == ["heuristic", "pptagent_local"]


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


def test_ai_cli_can_use_local_provider_when_mocked(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_local_deck.json"
    provider = get_provider("pptagent_local")

    fake_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
            {"type": "summary", "title": "Summary", "bullets": ["Keep scope tight"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    fake_analysis = {
        "image_suggestions": ["sales leadership dashboard"],
        "density_review": {"status": "ok", "warning_count": 0, "warnings": [], "slides": []},
    }

    monkeypatch.setattr(
        provider,
        "generate",
        lambda briefing, theme_name=None: BriefingGenerationResult(
            provider_name="pptagent_local",
            payload=fake_payload,
            analysis=fake_analysis,
        ),
    )

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--provider",
            "pptagent_local",
        ]
    )

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "AI copilots for sales teams"


def test_local_provider_timeout_surfaces_clear_error(monkeypatch) -> None:
    provider = get_provider("pptagent_local")

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["llama-cli"], timeout=1, output="partial json", stderr="")

    monkeypatch.setattr(subprocess, "run", _timeout)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/llama-cli")

    try:
        provider.run_model(Path("/tmp/fake.gguf"), "prompt")
    except RuntimeError as exc:
        assert "timed out" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when llama-cli times out")
