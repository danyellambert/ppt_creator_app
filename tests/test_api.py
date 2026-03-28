from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from urllib import request

from PIL import Image
from pptx import Presentation as PptxPresentation

from ppt_creator.api import build_api_server
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


def _request_json(url: str, payload: dict[str, object] | None = None, *, method: str = "GET"):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data is not None else {}
    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=5) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_api_health_and_templates_endpoints() -> None:
    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        status, health_payload = _request_json(f"{base_url}/health")
        assert status == 200
        assert health_payload["status"] == "ok"

        status, templates_payload = _request_json(f"{base_url}/templates")
        assert status == 200
        assert templates_payload["domains"] == ["consulting", "product", "sales", "strategy"]

        status, profiles_payload = _request_json(f"{base_url}/profiles")
        assert status == 200
        assert profiles_payload["profiles"]

        status, assets_payload = _request_json(f"{base_url}/assets")
        assert status == 200
        assert assets_payload["collections"]

        req = request.Request(f"{base_url}/playground", method="GET")
        with request.urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8")
        assert "PPT Creator Playground" in html
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_validate_render_and_template_endpoints(tmp_path: Path) -> None:
    from ppt_creator import preview as preview_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec_payload = PresentationInput.from_path("examples/ai_sales.json").model_dump(mode="json")

        status, validate_payload = _request_json(
            f"{base_url}/validate",
            {"spec": spec_payload, "check_assets": True},
            method="POST",
        )
        assert status == 200
        assert validate_payload["result"]["valid"] is True
        assert validate_payload["result"]["slide_count"] == len(spec_payload["slides"])

        output_path = tmp_path / "api_render_output.pptx"
        status, render_payload = _request_json(
            f"{base_url}/render",
            {
                "spec": spec_payload,
                "output_path": str(output_path),
                "dry_run": True,
                "include_review": True,
            },
            method="POST",
        )
        assert status == 200
        assert render_payload["result"]["rendered"] is False
        assert render_payload["result"]["output_path"].endswith("api_render_output.pptx")
        assert render_payload["result"]["quality_review"] is not None
        assert "clipping_risk_count" in render_payload["result"]["quality_review"]

        status, review_payload = _request_json(
            f"{base_url}/review",
            {"spec": spec_payload},
            method="POST",
        )
        assert status == 200
        assert review_payload["result"]["slide_count"] == len(spec_payload["slides"])
        assert review_payload["result"]["status"] in {"ok", "review", "attention"}
        assert "severity_counts" in review_payload["result"]
        assert "overflow_risk_count" in review_payload["result"]
        assert "clipping_risk_count" in review_payload["result"]
        assert "collision_risk_count" in review_payload["result"]
        assert "balance_warning_count" in review_payload["result"]
        assert "top_risk_slides" in review_payload["result"]

        status, template_payload = _request_json(
            f"{base_url}/template",
            {"domain": "sales", "theme_name": "consulting_clean", "audience_profile": "board"},
            method="POST",
        )
        assert status == 200
        assert template_payload["template"]["presentation"]["theme"] == "consulting_clean"
        assert template_payload["template"]["presentation"]["footer_text"] == "Board profile"

        preview_module.find_office_runtime = lambda: None
        preview_dir = tmp_path / "api_previews"
        status, preview_payload = _request_json(
            f"{base_url}/preview",
            {
                "spec": spec_payload,
                "output_dir": str(preview_dir),
                "basename": "api-preview",
                "debug_grid": True,
                "debug_safe_areas": True,
            },
            method="POST",
        )
        assert status == 200
        assert preview_payload["result"]["preview_count"] == len(spec_payload["slides"])
        assert preview_payload["result"]["quality_review"]["status"] in {"ok", "review"}
        assert "severity_counts" in preview_payload["result"]["quality_review"]
        assert "clipping_risk_count" in preview_payload["result"]["quality_review"]
        assert preview_payload["result"]["preview_artifact_review"]["status"] in {"ok", "review"}
        assert preview_payload["result"]["backend_requested"] == "auto"
        assert preview_payload["result"]["backend_used"] in {"synthetic", "office"}
        assert Path(preview_payload["result"]["thumbnail_sheet"]).exists()

        baseline_dir = tmp_path / "api_baseline_previews"
        status, baseline_preview_payload = _request_json(
            f"{base_url}/preview",
            {
                "spec": spec_payload,
                "output_dir": str(baseline_dir),
                "basename": "api-baseline",
            },
            method="POST",
        )
        assert status == 200
        assert baseline_preview_payload["result"]["preview_count"] == len(spec_payload["slides"])

        regression_dir = tmp_path / "api_regression_previews"
        status, regression_preview_payload = _request_json(
            f"{base_url}/preview",
            {
                "spec": spec_payload,
                "output_dir": str(regression_dir),
                "basename": "api-regression",
                "baseline_dir": str(baseline_dir),
                "write_diff_images": True,
            },
            method="POST",
        )
        assert status == 200
        assert regression_preview_payload["result"]["visual_regression"] is not None
        assert regression_preview_payload["result"]["visual_regression"]["diff_count"] == 0

        pptx_path = tmp_path / "api_preview_source.pptx"
        PresentationRenderer(asset_root="examples").render(PresentationInput.model_validate(spec_payload), pptx_path)

        def _fake_run(command, capture_output, text, check):
            outdir = Path(command[command.index("--outdir") + 1])
            source_pptx = Path(command[-1])
            slide_count = len(PptxPresentation(str(source_pptx)).slides)
            outdir.mkdir(parents=True, exist_ok=True)
            for index in range(1, slide_count + 1):
                Image.new("RGB", (1280, 720), (245, 245, 245)).save(outdir / f"api-mock-{index:02d}.png")

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        preview_module.find_office_runtime = lambda: "/usr/bin/soffice"
        preview_module.subprocess.run = _fake_run

        pptx_preview_dir = tmp_path / "api_preview_pptx_output"
        status, pptx_preview_payload = _request_json(
            f"{base_url}/preview-pptx",
            {
                "input_pptx": str(pptx_path),
                "output_dir": str(pptx_preview_dir),
            },
            method="POST",
        )
        assert status == 200
        assert pptx_preview_payload["result"]["mode"] == "preview-pptx"
        assert pptx_preview_payload["result"]["preview_count"] == len(spec_payload["slides"])
        assert pptx_preview_payload["result"]["backend_used"] == "office"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_render_can_generate_previews_from_rendered_pptx(tmp_path: Path) -> None:
    from ppt_creator import preview as preview_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec_payload = PresentationInput.from_path("examples/ai_sales.json").model_dump(mode="json")

        def _fake_run(command, capture_output, text, check):
            outdir = Path(command[command.index("--outdir") + 1])
            source_pptx = Path(command[-1])
            slide_count = len(PptxPresentation(str(source_pptx)).slides)
            outdir.mkdir(parents=True, exist_ok=True)
            for index in range(1, slide_count + 1):
                Image.new("RGB", (1280, 720), (245, 245, 245)).save(outdir / f"api-render-preview-{index:02d}.png")

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        preview_module.find_office_runtime = lambda: "/usr/bin/soffice"
        preview_module.subprocess.run = _fake_run

        output_path = tmp_path / "api_render_with_preview_output.pptx"
        preview_dir = tmp_path / "api_render_previews"
        status, render_payload = _request_json(
            f"{base_url}/render",
            {
                "spec": spec_payload,
                "output_path": str(output_path),
                "preview_output_dir": str(preview_dir),
            },
            method="POST",
        )

        assert status == 200
        assert render_payload["result"]["rendered"] is True
        assert render_payload["result"]["preview_output_dir"] == str(preview_dir)
        assert render_payload["result"]["preview_source"] == "rendered_pptx"
        assert render_payload["result"]["preview_result"]["mode"] == "preview-pptx"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_review_can_attach_preview_result_with_real_artifact_preference(tmp_path: Path) -> None:
    from ppt_creator import api as api_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec_payload = PresentationInput.from_path("examples/ai_sales.json").model_dump(mode="json")
        preview_dir = tmp_path / "api_review_previews"

        api_module.render_previews_for_rendered_artifact = lambda *args, **kwargs: (
            {
                "mode": "preview-pptx",
                "preview_count": 10,
                "previews": [],
                "thumbnail_sheet": str(preview_dir / "thumbs.png"),
                "preview_artifact_review": {"status": "ok"},
                "visual_regression": None,
                "backend_used": "office",
            },
            "rendered_pptx",
        )

        status, review_payload = _request_json(
            f"{base_url}/review",
            {
                "spec": spec_payload,
                "preview_output_dir": str(preview_dir),
            },
            method="POST",
        )
        assert status == 200
        assert review_payload["result"]["preview_source"] == "rendered_pptx"
        assert review_payload["result"]["preview_result"]["mode"] == "preview-pptx"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_preview_pptx_falls_back_to_pdf_rasterization_when_needed(tmp_path: Path) -> None:
    from ppt_creator import preview as preview_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec_payload = PresentationInput.from_path("examples/ai_sales.json").model_dump(mode="json")
        pptx_path = tmp_path / "api_preview_pdf_fallback_source.pptx"
        PresentationRenderer(asset_root="examples").render(PresentationInput.model_validate(spec_payload), pptx_path)

        def _fake_run(command, capture_output, text, check):
            outdir = Path(command[command.index("--outdir") + 1]) if "--outdir" in command else tmp_path
            outdir.mkdir(parents=True, exist_ok=True)
            if command[0] == "/usr/bin/soffice" and "png" in command:
                Image.new("RGB", (1280, 720), (245, 245, 245)).save(outdir / "single.png")
            elif command[0] == "/usr/bin/soffice" and "pdf" in command:
                (outdir / "api_preview_pdf_fallback_source.pdf").write_bytes(b"%PDF-1.4 mock")
            elif command[0] == "/usr/bin/gs":
                slide_count = len(PptxPresentation(str(pptx_path)).slides)
                pattern = next(argument.split("=", 1)[1] for argument in command if argument.startswith("-sOutputFile="))
                for index in range(1, slide_count + 1):
                    target = Path(pattern.replace("%02d", f"{index:02d}"))
                    Image.new("RGB", (1280, 720), (245, 245, 245)).save(target)

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        preview_module.find_office_runtime = lambda: "/usr/bin/soffice"
        preview_module.find_ghostscript_runtime = lambda: "/usr/bin/gs"
        preview_module.subprocess.run = _fake_run

        pptx_preview_dir = tmp_path / "api_preview_pdf_fallback_output"
        status, pptx_preview_payload = _request_json(
            f"{base_url}/preview-pptx",
            {
                "input_pptx": str(pptx_path),
                "output_dir": str(pptx_preview_dir),
            },
            method="POST",
        )
        assert status == 200
        assert pptx_preview_payload["result"]["preview_count"] == len(spec_payload["slides"])
        assert pptx_preview_payload["result"]["office_conversion_strategy"] == "pdf_via_ghostscript"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_compare_pptx_endpoint_generates_visual_comparison(tmp_path: Path) -> None:
    from ppt_creator import preview as preview_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec = PresentationInput.from_path("examples/ai_sales.json")
        before_pptx = tmp_path / "api_compare_before.pptx"
        after_pptx = tmp_path / "api_compare_after.pptx"
        PresentationRenderer(asset_root="examples").render(spec, before_pptx)
        PresentationRenderer(asset_root="examples").render(spec, after_pptx)

        def _fake_run(command, capture_output, text, check):
            outdir = Path(command[command.index("--outdir") + 1]) if "--outdir" in command else tmp_path
            source_pptx = Path(command[-1])
            slide_count = len(PptxPresentation(str(source_pptx)).slides)
            outdir.mkdir(parents=True, exist_ok=True)
            for index in range(1, slide_count + 1):
                Image.new("RGB", (1280, 720), (245, 245, 245)).save(outdir / f"api-compare-{index:02d}.png")

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        preview_module.find_office_runtime = lambda: "/usr/bin/soffice"
        preview_module.subprocess.run = _fake_run

        comparison_dir = tmp_path / "api_compare_output"
        status, comparison_payload = _request_json(
            f"{base_url}/compare-pptx",
            {
                "before_pptx": str(before_pptx),
                "after_pptx": str(after_pptx),
                "output_dir": str(comparison_dir),
                "write_diff_images": True,
            },
            method="POST",
        )
        assert status == 200
        assert comparison_payload["result"]["mode"] == "compare-pptx"
        assert comparison_payload["result"]["comparison"]["status"] == "ok"
        assert comparison_payload["result"]["comparison"]["diff_count"] == 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_review_pptx_endpoint_generates_real_artifact_review(tmp_path: Path) -> None:
    from ppt_creator import preview as preview_module

    server = build_api_server("127.0.0.1", 0, asset_root="examples")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        spec = PresentationInput.from_path("examples/ai_sales.json")
        pptx_path = tmp_path / "api_review_source.pptx"
        PresentationRenderer(asset_root="examples").render(spec, pptx_path)

        def _fake_run(command, capture_output, text, check):
            outdir = Path(command[command.index("--outdir") + 1])
            source_pptx = Path(command[-1])
            slide_count = len(PptxPresentation(str(source_pptx)).slides)
            outdir.mkdir(parents=True, exist_ok=True)
            for index in range(1, slide_count + 1):
                Image.new("RGB", (1280, 720), (245, 245, 245)).save(outdir / f"api-review-{index:02d}.png")

            class _Completed:
                returncode = 0
                stdout = ""
                stderr = ""

            return _Completed()

        preview_module.find_office_runtime = lambda: "/usr/bin/soffice"
        preview_module.subprocess.run = _fake_run

        review_dir = tmp_path / "api_review_pptx_output"
        status, review_payload = _request_json(
            f"{base_url}/review-pptx",
            {
                "input_pptx": str(pptx_path),
                "output_dir": str(review_dir),
            },
            method="POST",
        )
        assert status == 200
        assert review_payload["result"]["mode"] == "review-pptx"
        assert review_payload["result"]["preview_result"]["mode"] == "preview-pptx"
        assert "preview_artifact_review" in review_payload["result"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
