from __future__ import annotations

import json
from pathlib import Path

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.cli import main
from ppt_creator_ai.providers import get_provider
from ppt_creator_ai.providers.base import BriefingGenerationResult, DeckCritiqueResult


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
    assert provider_names == ["heuristic", "local_service", "ollama_local"]


def test_ai_cli_can_run_benchmark_and_emit_report(tmp_path: Path) -> None:
    output_dir = tmp_path / "benchmark_outputs"
    report = tmp_path / "benchmark_report.json"

    result = main([
        "benchmark",
        str(output_dir),
        "--provider",
        "heuristic",
        "--write-json-decks",
        "--report-json",
        str(report),
    ])

    assert result == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["scenario_count"] >= 4
    assert payload["successful_generations"] == payload["scenario_count"]
    assert payload["unique_slide_type_count"] >= 8
    assert payload["fallback_rate"] >= 0.0
    assert payload["fallback_used_count"] >= 0
    assert (output_dir / "sales_qbr_prompt.json").exists()


def test_ai_cli_can_write_analysis_report(tmp_path: Path) -> None:
    output = tmp_path / "generated_deck.json"
    analysis = tmp_path / "briefing_analysis.json"
    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--analysis-json",
        str(analysis),
    ])

    assert result == 0
    assert analysis.exists()

    payload = json.loads(analysis.read_text(encoding="utf-8"))
    assert payload["image_suggestions"]
    assert payload["density_review"]["status"] in {"ok", "review"}
    assert payload["generated_deck_review"]["status"] in {"ok", "review", "attention"}
    assert isinstance(payload["slide_critiques"], list)


def test_ai_cli_can_write_review_and_render_generated_pptx(tmp_path: Path) -> None:
    output_json = tmp_path / "generated_deck.json"
    review_json = tmp_path / "generated_deck_review.json"
    output_pptx = tmp_path / "generated_deck.pptx"

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output_json),
        "--review-json",
        str(review_json),
        "--render-pptx",
        str(output_pptx),
    ])

    assert result == 0
    assert output_json.exists()
    assert review_json.exists()
    assert output_pptx.exists()


def test_ai_cli_can_auto_refine_generated_deck(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_refined_deck.json"
    report = tmp_path / "generated_refined_report.json"
    provider = get_provider("heuristic")

    long_bullet = "This bullet is intentionally too long and too detailed for a clean executive slide so the refine pass should shorten it significantly."
    fake_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": [long_bullet] * 6},
            {"type": "summary", "title": "Summary", "body": "Dense summary", "bullets": [long_bullet] * 5},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    fake_analysis = {"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []}}

    monkeypatch.setattr(provider, "generate", lambda briefing, theme_name=None, feedback_messages=None: BriefingGenerationResult(provider_name="heuristic", payload=fake_payload, analysis=fake_analysis))

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--auto-refine",
        "--refine-passes",
        "2",
        "--report-json",
        str(report),
    ])

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_refine_enabled"] is True
    assert len(output_payload["slides"][1]["bullets"]) <= 4


def test_ai_cli_can_auto_regenerate_generated_deck(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_regenerated_deck.json"
    report = tmp_path / "generated_regenerated_report.json"
    provider = get_provider("heuristic")

    long_bullet = "This bullet is intentionally too long and too detailed for a clean executive slide so the regeneration pass should tighten it significantly."
    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": [long_bullet] * 6},
            {"type": "summary", "title": "Summary", "body": "Dense summary", "bullets": [long_bullet] * 5},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Tighter intro for an executive audience.", "bullets": ["Context", "Pilot scope", "Decision", "Metrics"]},
            {"type": "summary", "title": "Summary", "body": "Focused summary for the decision meeting.", "bullets": ["Start narrow", "Measure lift", "Scale winners"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        payload = improved_payload if feedback_messages else noisy_payload
        return BriefingGenerationResult(provider_name="heuristic", payload=payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []}})

    monkeypatch.setattr(provider, "generate", _generate)

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--auto-regenerate",
        "--regenerate-passes",
        "2",
        "--report-json",
        str(report),
    ])

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_regenerate_applied"] is True
    assert report_payload["regenerate_passes_completed"] >= 1
    assert output_payload["slides"][1]["body"] == "Tighter intro for an executive audience."


def test_ai_cli_auto_regenerate_can_use_preview_feedback(tmp_path: Path, monkeypatch) -> None:
    from ppt_creator_ai import cli as ai_cli_module

    output = tmp_path / "generated_preview_feedback_deck.json"
    report = tmp_path / "generated_preview_feedback_report.json"
    preview_dir = tmp_path / "generated_preview_feedback_previews"
    provider = get_provider("heuristic")

    seen_feedback_messages: list[str] = []
    long_bullet = "This bullet is intentionally too long and too detailed for a clean executive slide so the regeneration pass should tighten it significantly."
    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": [long_bullet] * 6},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Tighter intro for an executive audience.", "bullets": ["Context", "Pilot scope", "Decision", "Metrics"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        if feedback_messages:
            seen_feedback_messages.extend(feedback_messages)
        payload = improved_payload if feedback_messages else noisy_payload
        return BriefingGenerationResult(provider_name="heuristic", payload=payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []}})

    monkeypatch.setattr(provider, "generate", _generate)
    monkeypatch.setattr(ai_cli_module, "render_previews_for_rendered_artifact", lambda *args, **kwargs: ({"mode": "preview", "preview_count": 3, "previews": [], "thumbnail_sheet": str(preview_dir / "thumbs.png"), "quality_review": {"status": "review", "warning_count": 1}, "preview_artifact_review": {"status": "review", "edge_contact_count": 0, "edge_density_warning_count": 1, "body_edge_contact_count": 1, "safe_area_intrusion_count": 1, "footer_intrusion_count": 1, "corner_density_warning_count": 1}, "visual_regression": None, "backend_requested": kwargs.get("backend"), "backend_used": "synthetic"}, "spec"))

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--auto-regenerate",
        "--preview-dir",
        str(preview_dir),
        "--report-json",
        str(report),
    ])

    assert result == 0
    assert any("safe" in message.lower() or "footer" in message.lower() or "corner" in message.lower() for message in seen_feedback_messages)
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_regenerate_applied"] is True
    _ = json.loads((tmp_path / "generated_preview_feedback_report.json").read_text(encoding="utf-8")) if (tmp_path / "generated_preview_feedback_report.json").exists() else {}


def test_ai_cli_can_run_service_backed_review_after_qa(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_service_review_deck.json"
    report = tmp_path / "generated_service_review_report.json"
    provider = get_provider("local_service")

    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": ["Too many words"] * 5},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Sharper intro for the decision meeting.", "bullets": ["Context", "Pilot scope", "Decision", "Metrics"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    monkeypatch.setattr(provider, "generate", lambda briefing, theme_name=None, feedback_messages=None: BriefingGenerationResult(provider_name="local_service", payload=noisy_payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []}}))
    monkeypatch.setattr(provider, "revise_generated_deck", lambda briefing, current_payload, review, slide_critiques, theme_name=None, feedback_messages=None: BriefingGenerationResult(provider_name="local_service", payload=improved_payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "ok", "warning_count": 0, "warnings": [], "slides": []}, "revision_mode": "service_review"}))

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--provider",
        "local_service",
        "--auto-llm-review",
        "--report-json",
        str(report),
    ])

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_llm_review_applied"] is True
    assert report_payload["llm_review_passes_completed"] >= 1
    assert output_payload["slides"][1]["body"] == "Sharper intro for the decision meeting."


def test_ai_cli_analysis_report_includes_iteration_decisions(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_iteration_deck.json"
    analysis = tmp_path / "generated_iteration_analysis.json"
    provider = get_provider("heuristic")

    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": ["Too many words"] * 5},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Sharper intro", "bullets": ["Context", "Pilot scope", "Decision", "Metrics"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        payload = improved_payload if feedback_messages else noisy_payload
        return BriefingGenerationResult(provider_name="heuristic", payload=payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 1, "warnings": ["dense"], "slides": []}})

    monkeypatch.setattr(provider, "generate", _generate)

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--auto-regenerate",
        "--analysis-json",
        str(analysis),
    ])

    assert result == 0
    analysis_payload = json.loads(analysis.read_text(encoding="utf-8"))
    assert analysis_payload["regeneration_history"]
    assert analysis_payload["regeneration_history"][0]["decision"]


def test_ai_cli_can_emit_service_backed_slide_critiques(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_service_critiques_deck.json"
    report = tmp_path / "generated_service_critiques_report.json"
    critique_json = tmp_path / "generated_service_critiques.json"
    provider = get_provider("local_service")

    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "body": "Dense intro", "bullets": ["A very long bullet"] * 5},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    monkeypatch.setattr(provider, "generate", lambda briefing, theme_name=None, feedback_messages=None: BriefingGenerationResult(provider_name="local_service", payload=noisy_payload, analysis={"image_suggestions": ["sales leadership dashboard"], "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []}}))
    monkeypatch.setattr(provider, "critique_generated_deck", lambda briefing, current_payload, review, slide_critiques, theme_name=None, feedback_messages=None: DeckCritiqueResult(provider_name="local_service", critiques=[{"slide_number": 2, "slide_type": "agenda", "title": "Agenda", "risk_level": "high", "issues": ["Too many bullets", "Body is too dense"], "rewrite_guidance": ["Reduce to four bullets", "Shorten the narrative intro"], "visual_guidance": ["Create more whitespace above the footer"], "executive_tone_guidance": ["Use sharper decision-oriented language"]}], analysis={"provider": "local_service", "critique_mode": "service_slide_critique", "critique_count": 1}))

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output),
        "--provider",
        "local_service",
        "--llm-critique-json",
        str(critique_json),
        "--report-json",
        str(report),
    ])

    assert result == 0
    critique_payload = json.loads(critique_json.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert critique_payload["provider"] == "local_service"
    assert critique_payload["critiques"][0]["slide_number"] == 2
    assert report_payload["llm_slide_critique_count"] == 1


def test_ai_cli_can_generate_previews_for_generated_deck(tmp_path: Path) -> None:
    output_json = tmp_path / "generated_deck.json"
    preview_dir = tmp_path / "generated_previews"
    preview_report = tmp_path / "generated_preview_report.json"
    generation_report = tmp_path / "generated_report.json"

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output_json),
        "--preview-dir",
        str(preview_dir),
        "--preview-report-json",
        str(preview_report),
        "--report-json",
        str(generation_report),
    ])

    assert result == 0
    assert output_json.exists()
    assert preview_report.exists()
    preview_payload = json.loads(preview_report.read_text(encoding="utf-8"))
    generation_payload = json.loads(generation_report.read_text(encoding="utf-8"))
    assert preview_payload["preview_count"] >= 1
    assert generation_payload["preview_output_dir"] == str(preview_dir)


def test_ai_cli_prefers_rendered_pptx_preview_by_default_when_render_output_exists(tmp_path: Path, monkeypatch) -> None:
    from ppt_creator_ai import cli as ai_cli_module

    output_json = tmp_path / "generated_deck.json"
    output_pptx = tmp_path / "generated_deck.pptx"
    preview_dir = tmp_path / "generated_real_previews"
    report_path = tmp_path / "generated_report.json"

    captured: dict[str, object] = {}

    def _fake_render_previews_for_rendered_artifact(spec, output_dir, **kwargs):
        captured["rendered_pptx"] = str(kwargs.get("rendered_pptx")) if kwargs.get("rendered_pptx") else None
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return ({"mode": "preview-pptx", "preview_count": 8, "previews": [], "thumbnail_sheet": str(Path(output_dir) / "thumbs.png"), "quality_review": None, "preview_artifact_review": {"status": "ok"}, "visual_regression": None, "backend_requested": kwargs.get("backend"), "backend_used": "office"}, "rendered_pptx")

    monkeypatch.setattr(ai_cli_module, "render_previews_for_rendered_artifact", _fake_render_previews_for_rendered_artifact)

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output_json),
        "--render-pptx",
        str(output_pptx),
        "--preview-dir",
        str(preview_dir),
        "--report-json",
        str(report_path),
    ])

    assert result == 0
    assert captured["rendered_pptx"] == str(output_pptx)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["preview_source"] == "rendered_pptx"


def test_ai_cli_can_generate_previews_from_rendered_pptx(tmp_path: Path, monkeypatch) -> None:
    from ppt_creator_ai import cli as ai_cli_module

    output_json = tmp_path / "generated_deck.json"
    output_pptx = tmp_path / "generated_deck.pptx"
    preview_dir = tmp_path / "generated_real_previews"
    report_path = tmp_path / "generated_real_preview_report.json"

    captured: dict[str, object] = {}

    def _fake_render_previews_for_rendered_artifact(spec, output_dir, **kwargs):
        captured["input_pptx"] = str(kwargs.get("rendered_pptx"))
        captured["output_dir"] = str(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return ({"mode": "preview-pptx", "preview_count": 8, "previews": [], "thumbnail_sheet": str(Path(output_dir) / "thumbs.png"), "quality_review": None, "preview_artifact_review": {"status": "ok"}, "visual_regression": None, "backend_requested": kwargs.get("backend"), "backend_used": "office", "office_conversion_strategy": "pdf_via_ghostscript"}, "rendered_pptx")

    monkeypatch.setattr(ai_cli_module, "render_previews_for_rendered_artifact", _fake_render_previews_for_rendered_artifact)

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output_json),
        "--render-pptx",
        str(output_pptx),
        "--preview-dir",
        str(preview_dir),
        "--preview-from-rendered-pptx",
        "--preview-report-json",
        str(report_path),
    ])

    assert result == 0
    assert captured["input_pptx"] == str(output_pptx)
    assert captured["output_dir"] == str(preview_dir)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "preview-pptx"


def test_ai_cli_rejects_preview_from_rendered_pptx_without_render_flag(tmp_path: Path, capsys) -> None:
    output_json = tmp_path / "generated_deck.json"
    preview_dir = tmp_path / "generated_real_previews"

    result = main([
        "generate",
        "examples/briefing_sales.json",
        str(output_json),
        "--preview-dir",
        str(preview_dir),
        "--preview-from-rendered-pptx",
    ])
    captured = capsys.readouterr()

    assert result == 2
    assert "requires --render-pptx" in captured.err
