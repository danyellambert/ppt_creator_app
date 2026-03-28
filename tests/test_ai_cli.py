from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib import error

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import BriefingInput
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


def test_ai_cli_generates_deck_json_from_freeform_briefing_text(tmp_path: Path) -> None:
    input_path = tmp_path / "freeform_briefing.json"
    output = tmp_path / "generated_freeform_deck.json"
    input_path.write_text(
        json.dumps(
            {
                "title": "AI copilots for sales teams",
                "briefing_text": (
                    "Sales leaders are overloaded with repetitive preparation work and inconsistent storytelling. "
                    "We should start with one workflow for leadership meeting prep, measure time saved and quality lift, and only then expand scope."
                ),
            }
        ),
        encoding="utf-8",
    )

    result = main(["generate", str(input_path), str(output)])

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert len(spec.slides) >= 4
    assert any(slide.type.value == "summary" for slide in spec.slides)


def test_ai_cli_lists_available_providers(tmp_path: Path, capsys) -> None:
    report = tmp_path / "providers.json"
    result = main(["providers", "--report-json", str(report)])
    captured = capsys.readouterr()

    assert result == 0
    assert report.exists()
    assert "Available providers" in captured.out

    payload = json.loads(report.read_text(encoding="utf-8"))
    provider_names = [provider["name"] for provider in payload["providers"]]
    assert provider_names == ["anthropic", "heuristic", "ollama", "openai", "pptagent_local"]


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
    assert payload["generated_deck_review"]["status"] in {"ok", "review", "attention"}
    assert isinstance(payload["slide_critiques"], list)


def test_ai_cli_can_write_review_and_render_generated_pptx(tmp_path: Path) -> None:
    output_json = tmp_path / "generated_deck.json"
    review_json = tmp_path / "generated_deck_review.json"
    output_pptx = tmp_path / "generated_deck.pptx"

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output_json),
            "--review-json",
            str(review_json),
            "--render-pptx",
            str(output_pptx),
        ]
    )

    assert result == 0
    assert output_json.exists()
    assert review_json.exists()
    assert output_pptx.exists()

    review_payload = json.loads(review_json.read_text(encoding="utf-8"))
    assert review_payload["status"] in {"ok", "review", "attention"}


def test_ai_cli_can_auto_refine_generated_deck(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_refined_deck.json"
    report = tmp_path / "generated_refined_report.json"
    provider = get_provider("heuristic")

    long_bullet = (
        "This bullet is intentionally too long and too detailed for a clean executive slide so the refine pass should shorten it significantly."
    )
    fake_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "This introduction paragraph is intentionally verbose and dense so the QA review can flag the generated slide before the refine pass runs.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {
                "type": "summary",
                "title": "Summary",
                "body": "Another intentionally long narrative paragraph that should be reduced after the automatic refinement step is applied.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    fake_analysis = {
        "image_suggestions": ["sales leadership dashboard"],
        "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []},
    }

    monkeypatch.setattr(
        provider,
        "generate",
        lambda briefing, theme_name=None: BriefingGenerationResult(
            provider_name="heuristic",
            payload=fake_payload,
            analysis=fake_analysis,
        ),
    )

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--auto-refine",
            "--refine-passes",
            "2",
            "--report-json",
            str(report),
        ]
    )

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_refine_enabled"] is True
    assert report_payload["generated_deck_issue_count"] <= report_payload["initial_generated_deck_issue_count"]
    assert len(output_payload["slides"][1]["bullets"]) <= 4


def test_ai_cli_can_auto_regenerate_generated_deck(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_regenerated_deck.json"
    report = tmp_path / "generated_regenerated_report.json"
    provider = get_provider("heuristic")

    long_bullet = (
        "This bullet is intentionally too long and too detailed for a clean executive slide so the regeneration pass should tighten it significantly."
    )
    noisy_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "This introduction paragraph is intentionally verbose and dense so the provider regeneration loop has a clear reason to regenerate the deck.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {
                "type": "summary",
                "title": "Summary",
                "body": "Another intentionally dense paragraph that should improve once the provider receives review-based feedback.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "Tighter intro for an executive audience.",
                "bullets": ["Context", "Pilot scope", "Decision", "Metrics"],
            },
            {
                "type": "summary",
                "title": "Summary",
                "body": "Focused summary for the decision meeting.",
                "bullets": ["Start narrow", "Measure lift", "Scale winners"],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        payload = improved_payload if feedback_messages else noisy_payload
        return BriefingGenerationResult(
            provider_name="heuristic",
            payload=payload,
            analysis={
                "image_suggestions": ["sales leadership dashboard"],
                "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []},
            },
        )

    monkeypatch.setattr(provider, "generate", _generate)

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--auto-regenerate",
            "--regenerate-passes",
            "2",
            "--report-json",
            str(report),
        ]
    )

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_regenerate_enabled"] is True
    assert report_payload["auto_regenerate_applied"] is True
    assert report_payload["generated_deck_issue_count"] < report_payload["initial_generated_deck_issue_count"]
    assert output_payload["slides"][1]["body"] == "Tighter intro for an executive audience."


def test_ai_cli_auto_regenerate_can_use_preview_feedback(tmp_path: Path, monkeypatch) -> None:
    from ppt_creator_ai import cli as ai_cli_module

    output = tmp_path / "generated_preview_feedback_deck.json"
    report = tmp_path / "generated_preview_feedback_report.json"
    preview_dir = tmp_path / "generated_preview_feedback_previews"
    provider = get_provider("heuristic")

    seen_feedback_messages: list[str] = []
    long_bullet = (
        "This bullet is intentionally too long and too detailed for a clean executive slide so the regeneration pass should tighten it significantly."
    )
    noisy_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "This introduction paragraph is intentionally verbose and dense so the provider regeneration loop has a clear reason to regenerate the deck.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "Tighter intro for an executive audience.",
                "bullets": ["Context", "Pilot scope", "Decision", "Metrics"],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        if feedback_messages:
            seen_feedback_messages.extend(feedback_messages)
        payload = improved_payload if feedback_messages else noisy_payload
        return BriefingGenerationResult(
            provider_name="heuristic",
            payload=payload,
            analysis={
                "image_suggestions": ["sales leadership dashboard"],
                "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []},
            },
        )

    monkeypatch.setattr(provider, "generate", _generate)
    monkeypatch.setattr(
        ai_cli_module,
        "render_previews_for_rendered_artifact",
        lambda *args, **kwargs: (
            {
                "mode": "preview",
                "preview_count": 3,
                "previews": [],
                "thumbnail_sheet": str(preview_dir / "thumbs.png"),
                "quality_review": {"status": "review", "warning_count": 1},
                "preview_artifact_review": {
                    "status": "review",
                    "edge_contact_count": 0,
                    "edge_density_warning_count": 1,
                    "body_edge_contact_count": 1,
                    "safe_area_intrusion_count": 1,
                    "footer_intrusion_count": 1,
                    "corner_density_warning_count": 1,
                },
                "visual_regression": None,
                "backend_requested": kwargs.get("backend"),
                "backend_used": "synthetic",
            },
            "spec",
        ),
    )

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--auto-regenerate",
            "--preview-dir",
            str(preview_dir),
            "--report-json",
            str(report),
        ]
    )

    assert result == 0
    assert any("safe" in message.lower() or "footer" in message.lower() or "corner" in message.lower() for message in seen_feedback_messages)
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_regenerate_applied"] is True


def test_ai_cli_combines_regeneration_and_refine_from_latest_review(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_combo_deck.json"
    report = tmp_path / "generated_combo_report.json"
    provider = get_provider("heuristic")

    long_bullet = (
        "This bullet is intentionally too long and too detailed for a clean executive slide and should clearly trigger density review."
    )
    verbose_body = (
        "This narrative paragraph is intentionally very long and repetitive so that the heuristic QA layer clearly flags it as too dense for an executive audience. "
        "It keeps adding more words about scope, process, structure, coordination, metrics, enablement, adoption, alignment, sequencing, governance, and risk until the body crosses the density threshold for a single agenda slide."
    )
    first_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": verbose_body,
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    regenerated_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": (
                    "Regenerated intro that is much better than the first draft but still a little too verbose for the final executive pass, so the refine step should shorten it further before export and remove excess narrative detail that still makes this agenda slide feel slightly denser than ideal for an executive audience."
                ),
                "bullets": [
                    "Context and scope with extra wording for density",
                    "Pilot design with more narrative detail",
                    "Decision framing with more context than necessary",
                    "Measurement plan with verbose explanation",
                    "Risk controls with additional qualifiers",
                ],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    def _generate(briefing, theme_name=None, feedback_messages=None):
        payload = regenerated_payload if feedback_messages else first_payload
        return BriefingGenerationResult(
            provider_name="heuristic",
            payload=payload,
            analysis={
                "image_suggestions": ["sales leadership dashboard"],
                "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []},
            },
        )

    monkeypatch.setattr(provider, "generate", _generate)

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--auto-regenerate",
            "--auto-refine",
            "--report-json",
            str(report),
        ]
    )

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_regenerate_applied"] is True
    assert report_payload["auto_refine_applied"] is True
    assert len(output_payload["slides"][1]["bullets"]) <= 4


def test_ai_cli_can_run_provider_backed_llm_review_after_qa(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_llm_review_deck.json"
    report = tmp_path / "generated_llm_review_report.json"
    provider = get_provider("openai")

    long_bullet = (
        "This bullet is intentionally too long and too detailed for a clean executive slide so the provider-backed review pass should tighten it significantly."
    )
    noisy_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "This introduction paragraph is intentionally verbose and dense so the LLM review loop has a clear reason to rewrite the deck.",
                "bullets": [long_bullet, long_bullet, long_bullet, long_bullet, long_bullet, long_bullet],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    improved_payload = {
        "presentation": {"title": "AI copilots for sales teams", "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {
                "type": "agenda",
                "title": "Agenda",
                "body": "Sharper intro for the decision meeting.",
                "bullets": ["Context", "Pilot scope", "Decision", "Metrics"],
            },
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }

    monkeypatch.setattr(
        provider,
        "generate",
        lambda briefing, theme_name=None, feedback_messages=None: BriefingGenerationResult(
            provider_name="openai",
            payload=noisy_payload,
            analysis={
                "image_suggestions": ["sales leadership dashboard"],
                "density_review": {"status": "review", "warning_count": 2, "warnings": ["dense"], "slides": []},
            },
        ),
    )
    monkeypatch.setattr(
        provider,
        "revise_generated_deck",
        lambda briefing, current_payload, review, slide_critiques, theme_name=None, feedback_messages=None: BriefingGenerationResult(
            provider_name="openai",
            payload=improved_payload,
            analysis={
                "image_suggestions": ["sales leadership dashboard"],
                "density_review": {"status": "ok", "warning_count": 0, "warnings": [], "slides": []},
                "revision_mode": "llm_review",
            },
        ),
    )

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output),
            "--provider",
            "openai",
            "--auto-llm-review",
            "--llm-review-passes",
            "2",
            "--report-json",
            str(report),
        ]
    )

    assert result == 0
    output_payload = json.loads(output.read_text(encoding="utf-8"))
    report_payload = json.loads(report.read_text(encoding="utf-8"))
    assert report_payload["auto_llm_review_enabled"] is True
    assert report_payload["auto_llm_review_applied"] is True
    assert report_payload["generated_deck_issue_count"] <= report_payload["initial_generated_deck_issue_count"]
    assert output_payload["slides"][1]["body"] == "Sharper intro for the decision meeting."


def test_ai_cli_can_generate_previews_for_generated_deck(tmp_path: Path) -> None:
    output_json = tmp_path / "generated_deck.json"
    preview_dir = tmp_path / "generated_previews"
    preview_report = tmp_path / "generated_preview_report.json"
    generation_report = tmp_path / "generated_report.json"

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output_json),
            "--preview-dir",
            str(preview_dir),
            "--preview-report-json",
            str(preview_report),
            "--report-json",
            str(generation_report),
        ]
    )

    assert result == 0
    assert output_json.exists()
    assert preview_report.exists()
    preview_payload = json.loads(preview_report.read_text(encoding="utf-8"))
    generation_payload = json.loads(generation_report.read_text(encoding="utf-8"))
    assert preview_payload["preview_count"] >= 1
    assert preview_payload["quality_review"]["status"] in {"ok", "review"}
    assert preview_payload["preview_artifact_review"]["status"] in {"ok", "review"}
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
        captured["backend"] = kwargs.get("backend")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        return (
            {
                "mode": "preview-pptx",
                "preview_count": 8,
                "previews": [],
                "thumbnail_sheet": str(Path(output_dir) / "thumbs.png"),
                "quality_review": None,
                "preview_artifact_review": {"status": "ok"},
                "visual_regression": None,
                "backend_requested": kwargs.get("backend"),
                "backend_used": "office",
            },
            "rendered_pptx",
        )

    monkeypatch.setattr(ai_cli_module, "render_previews_for_rendered_artifact", _fake_render_previews_for_rendered_artifact)

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output_json),
            "--render-pptx",
            str(output_pptx),
            "--preview-dir",
            str(preview_dir),
            "--report-json",
            str(report_path),
        ]
    )

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
        return (
            {
                "mode": "preview-pptx",
                "preview_count": 8,
                "previews": [],
                "thumbnail_sheet": str(Path(output_dir) / "thumbs.png"),
                "quality_review": None,
                "preview_artifact_review": {"status": "ok"},
                "visual_regression": None,
                "backend_requested": kwargs.get("backend"),
                "backend_used": "office",
                "office_conversion_strategy": "pdf_via_ghostscript",
            },
            "rendered_pptx",
        )

    monkeypatch.setattr(ai_cli_module, "render_previews_for_rendered_artifact", _fake_render_previews_for_rendered_artifact)

    result = main(
        [
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
        ]
    )

    assert result == 0
    assert captured["input_pptx"] == str(output_pptx)
    assert captured["output_dir"] == str(preview_dir)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["mode"] == "preview-pptx"


def test_ai_cli_rejects_preview_from_rendered_pptx_without_render_flag(tmp_path: Path, capsys) -> None:
    output_json = tmp_path / "generated_deck.json"
    preview_dir = tmp_path / "generated_real_previews"

    result = main(
        [
            "generate",
            "examples/briefing_sales.json",
            str(output_json),
            "--preview-dir",
            str(preview_dir),
            "--preview-from-rendered-pptx",
        ]
    )
    captured = capsys.readouterr()

    assert result == 2
    assert "requires --render-pptx" in captured.err


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


def test_ai_cli_can_use_ollama_provider_when_mocked(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_ollama_deck.json"
    provider = get_provider("ollama")

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
            provider_name="ollama",
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
            "ollama",
        ]
    )

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "AI copilots for sales teams"


def test_ai_cli_can_use_openai_provider_when_mocked(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_openai_deck.json"
    provider = get_provider("openai")

    fake_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
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
            provider_name="openai",
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
            "openai",
        ]
    )

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "AI copilots for sales teams"


def test_ai_cli_can_use_anthropic_provider_when_mocked(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "generated_anthropic_deck.json"
    provider = get_provider("anthropic")

    fake_payload = {
        "presentation": {
            "title": "AI copilots for sales teams",
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": "AI copilots for sales teams"},
            {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
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
            provider_name="anthropic",
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
            "anthropic",
        ]
    )

    assert result == 0
    spec = PresentationInput.from_path(output)
    assert spec.presentation.title == "AI copilots for sales teams"


def test_local_provider_timeout_surfaces_clear_error(monkeypatch) -> None:
    provider = get_provider("pptagent_local")

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=["llama-cli"], timeout=1, output=b"partial json", stderr=b"")

    monkeypatch.setattr(subprocess, "run", _timeout)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/local/bin/llama-cli")

    try:
        provider.run_model(Path("/tmp/fake.gguf"), "prompt")
    except RuntimeError as exc:
        assert "timed out" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when llama-cli times out")


def test_local_provider_prefers_llama_completion_for_one_shot(monkeypatch) -> None:
    provider = get_provider("pptagent_local")
    captured: dict[str, object] = {}

    class _Completed:
        returncode = 0
        stdout = "{}"
        stderr = ""

    def _which(name: str):
        if name == "llama-completion":
            return "/opt/homebrew/bin/llama-completion"
        if name == "llama-cli":
            return "/opt/homebrew/bin/llama-cli"
        return None

    def _run(command, **kwargs):
        captured["command"] = command
        return _Completed()

    monkeypatch.setattr("shutil.which", _which)
    monkeypatch.setattr(subprocess, "run", _run)

    provider.run_model(Path("/tmp/fake.gguf"), "prompt")

    command = captured["command"]
    assert command[0].endswith("llama-completion")
    assert "-no-cnv" in command
    assert "--simple-io" in command


def test_local_provider_normalizes_pptagent_style_payload() -> None:
    provider = get_provider("pptagent_local")

    raw_payload = {
        "presentation": {
            "slides": [
                {
                    "slide": "title",
                    "data": {
                        "title": "AI copilots for sales teams",
                        "subtitle": "Briefing to Executive Narrative",
                        "client_name": "Acme Revenue Team",
                        "author": "PPT Creator AI",
                        "date": "2026-03-26",
                    },
                },
                {
                    "slide": "section",
                    "data": {
                        "section": "Situation Overview",
                        "content": "Commercial teams want measurable productivity lift.",
                    },
                },
                {
                    "slide": "milestones",
                    "data": {
                        "milestones": [
                            {"title": "Diagnose", "detail": "Find the workflow", "phase": "Month 1"},
                            {"title": "Pilot", "detail": "Run the pilot", "phase": "Month 2"},
                        ]
                    },
                },
                {
                    "slide": "faq",
                    "data": {
                        "faqs": [
                            {"question": "Where do we start?", "answer": "Start narrow."},
                            {"question": "How do we measure success?", "answer": "Track lift."},
                        ]
                    },
                },
                {
                    "slide": "closing",
                    "data": {"closing_quote": "Stay structured."},
                },
            ]
        }
    }

    briefing_input = BriefingInput.from_path("examples/briefing_sales.json")
    normalized = provider.normalize_generated_payload(raw_payload, briefing_input)

    spec = PresentationInput.model_validate(normalized)
    assert spec.presentation.title == "AI copilots for sales teams"
    assert any(slide.type.value == "timeline" for slide in spec.slides)
    assert any(slide.type.value == "faq" for slide in spec.slides)
    assert any(slide.type.value == "bullets" for slide in spec.slides)


def test_ollama_provider_normalizes_mocked_json_payload(monkeypatch) -> None:
    provider = get_provider("ollama")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    monkeypatch.setattr(
        provider,
        "request_generation",
        lambda prompt, model_name: json.dumps(
            {
                "presentation": {
                    "title": "AI copilots for sales teams",
                    "slides": [
                        {"slide": "title", "data": {"title": "AI copilots for sales teams"}},
                        {"slide": "agenda", "data": {"title": "Agenda", "bullets": ["Context", "Decision"]}},
                        {"slide": "closing", "data": {"closing_quote": "Stay structured."}},
                    ],
                }
            }
        ),
    )

    result = provider.generate(briefing)

    spec = PresentationInput.model_validate(result.payload)
    assert spec.presentation.title == "AI copilots for sales teams"
    assert any(slide.type.value == "agenda" for slide in spec.slides)


def test_ollama_provider_surfaces_connection_error(monkeypatch) -> None:
    provider = get_provider("ollama")

    def _url_error(*args, **kwargs):
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _url_error)

    try:
        provider.request_generation("prompt", model_name="llama3.1")
    except RuntimeError as exc:
        assert "ollama serve" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when Ollama is unreachable")


def test_openai_provider_normalizes_mocked_json_payload(monkeypatch) -> None:
    provider = get_provider("openai")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    monkeypatch.setattr(
        provider,
        "request_generation",
        lambda prompt, model_name: json.dumps(
            {
                "presentation": {
                    "title": "AI copilots for sales teams",
                    "slides": [
                        {"slide": "title", "data": {"title": "AI copilots for sales teams"}},
                        {"slide": "agenda", "data": {"title": "Agenda", "bullets": ["Context", "Decision"]}},
                        {"slide": "closing", "data": {"closing_quote": "Stay structured."}},
                    ],
                }
            }
        ),
    )

    result = provider.generate(briefing)

    spec = PresentationInput.model_validate(result.payload)
    assert spec.presentation.title == "AI copilots for sales teams"
    assert any(slide.type.value == "agenda" for slide in spec.slides)


def test_openai_provider_requires_api_key(monkeypatch) -> None:
    provider = get_provider("openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PPT_CREATOR_AI_OPENAI_API_KEY", raising=False)

    try:
        provider.request_generation("prompt", model_name="gpt-4o-mini")
    except RuntimeError as exc:
        assert "OpenAI API key" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when OpenAI API key is missing")


def test_anthropic_provider_normalizes_mocked_json_payload(monkeypatch) -> None:
    provider = get_provider("anthropic")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    monkeypatch.setattr(
        provider,
        "request_generation",
        lambda prompt, model_name: json.dumps(
            {
                "presentation": {
                    "title": "AI copilots for sales teams",
                    "slides": [
                        {"slide": "title", "data": {"title": "AI copilots for sales teams"}},
                        {"slide": "agenda", "data": {"title": "Agenda", "bullets": ["Context", "Decision"]}},
                        {"slide": "closing", "data": {"closing_quote": "Stay structured."}},
                    ],
                }
            }
        ),
    )

    result = provider.generate(briefing)

    spec = PresentationInput.model_validate(result.payload)
    assert spec.presentation.title == "AI copilots for sales teams"
    assert any(slide.type.value == "agenda" for slide in spec.slides)


def test_anthropic_provider_requires_api_key(monkeypatch) -> None:
    provider = get_provider("anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PPT_CREATOR_AI_ANTHROPIC_API_KEY", raising=False)

    try:
        provider.request_generation("prompt", model_name="claude-3-5-haiku-latest")
    except RuntimeError as exc:
        assert "Anthropic API key" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when Anthropic API key is missing")
