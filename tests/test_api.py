from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
from urllib import request

from ppt_creator.api import build_api_server
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
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_validate_render_and_template_endpoints(tmp_path: Path) -> None:
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
            },
            method="POST",
        )
        assert status == 200
        assert render_payload["result"]["rendered"] is False
        assert render_payload["result"]["output_path"].endswith("api_render_output.pptx")

        status, template_payload = _request_json(
            f"{base_url}/template",
            {"domain": "sales", "theme_name": "consulting_clean"},
            method="POST",
        )
        assert status == 200
        assert template_payload["template"]["presentation"]["theme"] == "consulting_clean"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
