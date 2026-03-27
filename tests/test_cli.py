from __future__ import annotations

import json
from pathlib import Path

from ppt_creator.cli import main
from ppt_creator.schema import PresentationInput


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


def test_cli_review_generates_report(tmp_path: Path, capsys) -> None:
    report_path = tmp_path / "review_report.json"
    result = main(["review", "examples/ai_sales.json", "--report-json", str(report_path)])
    captured = capsys.readouterr()

    assert result == 0
    assert report_path.exists()
    assert "Review completed" in captured.out


def test_cli_validate_emits_informational_logs(capsys) -> None:
    result = main(["validate", "examples/product_strategy.json"])
    captured = capsys.readouterr()

    assert result == 0
    assert "[INFO] Loading input:" in captured.out
    assert "[OK] Valid JSON:" in captured.out


def test_cli_render_dry_run_does_not_create_file(tmp_path: Path, capsys) -> None:
    output = tmp_path / "dry_run_output.pptx"
    result = main(["render", "examples/ai_sales.json", str(output), "--dry-run"])
    captured = capsys.readouterr()

    assert result == 0
    assert not output.exists()
    assert "Dry run" in captured.out


def test_cli_render_batch_generates_output_and_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "batch_output"
    report_path = tmp_path / "batch_report.json"

    result = main(
        [
            "render-batch",
            "examples",
            str(output_dir),
            "--pattern",
            "product_strategy.json",
            "--report-json",
            str(report_path),
        ]
    )

    assert result == 0
    assert (output_dir / "product_strategy.pptx").exists()
    assert report_path.exists()


def test_cli_render_dry_run_accepts_theme_color_overrides(tmp_path: Path, capsys) -> None:
    output = tmp_path / "brand_override.pptx"
    result = main(
        [
            "render",
            "examples/ai_sales.json",
            str(output),
            "--dry-run",
            "--theme",
            "dark_boardroom",
            "--primary-color",
            "112233",
            "--secondary-color",
            "AABBCC",
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert not output.exists()
    assert "Dry run" in captured.out


def test_cli_template_generates_domain_json(tmp_path: Path, capsys) -> None:
    output = tmp_path / "sales_template.json"
    result = main(["template", "sales", str(output)])
    captured = capsys.readouterr()

    assert result == 0
    assert output.exists()
    assert "Generated template" in captured.out

    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "Sales operating review"
    assert len(spec.slides) >= 4


def test_cli_template_accepts_theme_override(tmp_path: Path) -> None:
    output = tmp_path / "strategy_template.json"
    result = main(["template", "strategy", str(output), "--theme", "consulting_clean"])

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert spec.presentation.theme == "consulting_clean"


def test_cli_preview_generates_pngs_and_thumbnail_sheet(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "preview_output"
    report_path = tmp_path / "preview_report.json"

    result = main(
        [
            "preview",
            "examples/ai_sales.json",
            str(output_dir),
            "--basename",
            "ai-sales-preview",
            "--report-json",
            str(report_path),
        ]
    )
    captured = capsys.readouterr()

    assert result == 0
    assert report_path.exists()
    assert "Generated previews" in captured.out
    report = report_path.read_text(encoding="utf-8")
    assert "quality_review" in report
    generated_pngs = sorted(output_dir.glob("*.png"))
    assert len(generated_pngs) == 11
    assert any(path.name.endswith("-thumbnails.png") for path in generated_pngs)


def test_cli_preview_accepts_debug_overlays(tmp_path: Path) -> None:
    output_dir = tmp_path / "preview_debug_output"
    result = main(
        [
            "preview",
            "examples/ai_sales.json",
            str(output_dir),
            "--debug-grid",
            "--debug-safe-areas",
        ]
    )

    assert result == 0
    assert sorted(output_dir.glob("*.png"))


def test_cli_preview_auto_backend_reports_synthetic_fallback(tmp_path: Path, monkeypatch) -> None:
    from ppt_creator import preview as preview_module

    monkeypatch.setattr(preview_module, "find_office_runtime", lambda: None)
    output_dir = tmp_path / "preview_auto_output"
    report_path = tmp_path / "preview_auto_report.json"

    result = main(
        [
            "preview",
            "examples/ai_sales.json",
            str(output_dir),
            "--report-json",
            str(report_path),
        ]
    )

    assert result == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["backend_requested"] == "auto"
    assert payload["backend_used"] == "synthetic"
