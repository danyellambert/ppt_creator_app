from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pydantic import ValidationError

from ppt_creator.preview import render_previews
from ppt_creator.qa import review_presentation
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput
from ppt_creator.templates import build_domain_template, list_template_domains


class APIRequestError(ValueError):
    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status_code = status_code


def _resolve_service_asset_root(asset_root: str | Path | None) -> Path:
    return Path(asset_root or ".").resolve()


def _extract_spec_payload(payload: dict[str, object]) -> dict[str, object]:
    if "spec" in payload:
        spec_payload = payload["spec"]
        if not isinstance(spec_payload, dict):
            raise APIRequestError("'spec' must be a JSON object")
        return spec_payload

    if "presentation" in payload and "slides" in payload:
        return {
            "presentation": payload["presentation"],
            "slides": payload["slides"],
        }

    raise APIRequestError("Request must include 'spec' or top-level presentation/slides")


def validate_spec_payload(
    spec_payload: dict[str, object],
    *,
    asset_root: str | Path | None = None,
    check_assets: bool = False,
) -> dict[str, object]:
    spec = PresentationInput.model_validate(spec_payload)
    missing_assets: list[str] = []

    if check_assets:
        renderer = PresentationRenderer(
            theme_name=spec.presentation.theme,
            asset_root=_resolve_service_asset_root(asset_root),
        )
        missing_assets = renderer.collect_missing_assets(spec)

    return {
        "mode": "validate",
        "valid": True,
        "presentation_title": spec.presentation.title,
        "theme": spec.presentation.theme,
        "slide_count": len(spec.slides),
        "missing_asset_count": len(missing_assets),
        "missing_assets": missing_assets,
    }


def render_spec_payload(
    spec_payload: dict[str, object],
    *,
    output_path: str | Path,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    dry_run: bool = False,
    check_assets: bool = False,
) -> dict[str, object]:
    spec = PresentationInput.model_validate(spec_payload)
    effective_theme = theme_name or spec.presentation.theme
    renderer = PresentationRenderer(
        theme_name=effective_theme,
        asset_root=_resolve_service_asset_root(asset_root),
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    destination = renderer.validate_output_path(output_path)
    missing_assets = renderer.collect_missing_assets(spec)

    if dry_run:
        return {
            "mode": "render",
            "rendered": False,
            "dry_run": True,
            "output_path": str(destination),
            "presentation_title": spec.presentation.title,
            "theme": effective_theme,
            "slide_count": len(spec.slides),
            "missing_asset_count": len(missing_assets) if check_assets else 0,
            "missing_assets": missing_assets if check_assets else [],
        }

    rendered_output = renderer.render(spec, destination)
    return {
        "mode": "render",
        "rendered": True,
        "dry_run": False,
        "output_path": str(rendered_output),
        "presentation_title": spec.presentation.title,
        "theme": effective_theme,
        "slide_count": len(spec.slides),
        "missing_asset_count": len(missing_assets) if check_assets else 0,
        "missing_assets": missing_assets if check_assets else [],
    }


def review_spec_payload(
    spec_payload: dict[str, object],
    *,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
) -> dict[str, object]:
    spec = PresentationInput.model_validate(spec_payload)
    return review_presentation(
        spec,
        theme_name=theme_name or spec.presentation.theme,
        asset_root=_resolve_service_asset_root(asset_root),
    )


def preview_spec_payload(
    spec_payload: dict[str, object],
    *,
    output_dir: str | Path,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    basename: str | None = None,
    debug_grid: bool = False,
    debug_safe_areas: bool = False,
    backend: str = "auto",
) -> dict[str, object]:
    spec = PresentationInput.model_validate(spec_payload)
    effective_theme = theme_name or spec.presentation.theme
    return render_previews(
        spec,
        output_dir,
        theme_name=effective_theme,
        asset_root=_resolve_service_asset_root(asset_root),
        primary_color=primary_color,
        secondary_color=secondary_color,
        basename=basename,
        debug_grid=debug_grid,
        debug_safe_areas=debug_safe_areas,
        backend=backend,
    )


def build_api_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    asset_root: str | Path | None = None,
) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), PptCreatorAPIHandler)
    server.asset_root = _resolve_service_asset_root(asset_root)
    return server


def serve_api(
    host: str = "127.0.0.1",
    port: int = 8787,
    *,
    asset_root: str | Path | None = None,
) -> None:
    server = build_api_server(host, port, asset_root=asset_root)
    try:
        print(f"[OK] API server listening on http://{host}:{server.server_address[1]}")
        server.serve_forever()
    except KeyboardInterrupt:
        print("[INFO] API server interrupted")
    finally:
        server.server_close()


class PptCreatorAPIHandler(BaseHTTPRequestHandler):
    server_version = "ppt-creator-api/0.1"

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _json_response(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, object]:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            raise APIRequestError("Request body is required")

        raw_body = self.rfile.read(content_length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise APIRequestError(f"Invalid JSON body: {exc.msg}") from exc

        if not isinstance(payload, dict):
            raise APIRequestError("Request body must be a JSON object")
        return payload

    def _handle_exception(self, exc: Exception) -> None:
        if isinstance(exc, APIRequestError):
            self._json_response(exc.status_code, {"error": str(exc)})
            return
        if isinstance(exc, ValidationError):
            self._json_response(HTTPStatus.BAD_REQUEST, {"error": exc.errors()})
            return
        self._json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json_response(HTTPStatus.OK, {"status": "ok"})
            return
        if self.path == "/templates":
            self._json_response(HTTPStatus.OK, {"domains": list_template_domains()})
            return
        self._json_response(HTTPStatus.NOT_FOUND, {"error": "Route not found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = self._read_json_body()
            default_asset_root = getattr(self.server, "asset_root", Path(".").resolve())

            if self.path == "/validate":
                spec_payload = _extract_spec_payload(payload)
                result = validate_spec_payload(
                    spec_payload,
                    asset_root=payload.get("asset_root") or default_asset_root,
                    check_assets=bool(payload.get("check_assets", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/render":
                if "output_path" not in payload:
                    raise APIRequestError("'output_path' is required for /render")
                spec_payload = _extract_spec_payload(payload)
                result = render_spec_payload(
                    spec_payload,
                    output_path=str(payload["output_path"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    asset_root=payload.get("asset_root") or default_asset_root,
                    primary_color=str(payload["primary_color"]) if payload.get("primary_color") else None,
                    secondary_color=str(payload["secondary_color"]) if payload.get("secondary_color") else None,
                    dry_run=bool(payload.get("dry_run", False)),
                    check_assets=bool(payload.get("check_assets", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/review":
                spec_payload = _extract_spec_payload(payload)
                result = review_spec_payload(
                    spec_payload,
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    asset_root=payload.get("asset_root") or default_asset_root,
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/preview":
                if "output_dir" not in payload:
                    raise APIRequestError("'output_dir' is required for /preview")
                spec_payload = _extract_spec_payload(payload)
                result = preview_spec_payload(
                    spec_payload,
                    output_dir=str(payload["output_dir"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    asset_root=payload.get("asset_root") or default_asset_root,
                    primary_color=str(payload["primary_color"]) if payload.get("primary_color") else None,
                    secondary_color=str(payload["secondary_color"]) if payload.get("secondary_color") else None,
                    basename=str(payload["basename"]) if payload.get("basename") else None,
                    debug_grid=bool(payload.get("debug_grid", False)),
                    debug_safe_areas=bool(payload.get("debug_safe_areas", False)),
                    backend=str(payload["preview_backend"]) if payload.get("preview_backend") else "auto",
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/template":
                if "domain" not in payload:
                    raise APIRequestError("'domain' is required for /template")
                template_payload = build_domain_template(
                    str(payload["domain"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                )
                self._json_response(HTTPStatus.OK, {"template": template_payload})
                return

            self._json_response(HTTPStatus.NOT_FOUND, {"error": "Route not found"})
        except Exception as exc:  # noqa: BLE001
            self._handle_exception(exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a lightweight HTTP API for PPT Creator.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8787, help="Port to listen on")
    parser.add_argument("--asset-root", help="Default asset root for API requests")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    serve_api(args.host, args.port, asset_root=args.asset_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
