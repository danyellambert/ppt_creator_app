from __future__ import annotations

from pathlib import Path

from ppt_creator.cli import main


def test_cli_render_generates_file(tmp_path: Path) -> None:
    output = tmp_path / "cli_output.pptx"
    result = main(["render", "examples/ai_sales.json", str(output)])
    assert result == 0
    assert output.exists()


def test_cli_returns_error_for_missing_input(capsys) -> None:
    result = main(["validate", "examples/missing.json"])
    captured = capsys.readouterr()

    assert result == 2
    assert "Input JSON not found" in captured.err


def test_cli_returns_error_for_invalid_output_extension(tmp_path: Path, capsys) -> None:
    output = tmp_path / "cli_output.txt"
    result = main(["render", "examples/ai_sales.json", str(output)])
    captured = capsys.readouterr()

    assert result == 2
    assert "must end with .pptx" in captured.err


def test_cli_validate_second_example() -> None:
    result = main(["validate", "examples/product_strategy.json"])
    assert result == 0
