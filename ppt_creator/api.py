from __future__ import annotations

import argparse
import json
import mimetypes
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse

from pydantic import ValidationError

from ppt_creator.assets import get_asset_collection, list_asset_collections
from ppt_creator.preview import (
    compare_pptx_artifacts,
    render_previews,
    render_previews_for_rendered_artifact,
    render_previews_from_pptx,
    review_pptx_artifact,
)
from ppt_creator.profiles import get_audience_profile, list_audience_profiles
from ppt_creator.qa import augment_review_with_preview_artifacts, review_presentation
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput
from ppt_creator.templates import build_domain_template, list_template_domains
from ppt_creator.workflows import build_workflow_packet, get_workflow_preset, list_workflow_presets


class APIRequestError(ValueError):
    def __init__(self, message: str, status_code: int = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status_code = status_code


def _build_playground_html() -> str:
    default_spec = build_domain_template("sales")
    initial_json = json.dumps(default_spec, indent=2, ensure_ascii=False)
    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <title>PPT Creator Playground</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; background: #f6f4f0; color: #14263f; }}
    textarea {{ width: 100%; min-height: 380px; font-family: monospace; font-size: 13px; }}
    input {{ width: 100%; padding: 8px; margin: 4px 0 12px; }}
    select {{ width: 100%; padding: 8px; margin: 4px 0 12px; }}
    button {{ margin-right: 8px; padding: 10px 14px; }}
    pre {{ background: white; border: 1px solid #d9dce2; padding: 16px; overflow: auto; max-height: 360px; }}
    .row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .toolbar {{ margin: 16px 0; display: flex; flex-wrap: wrap; gap: 8px; }}
    .status {{ margin-top: 12px; color: #44576d; font-size: 14px; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin-top: 20px; }}
    .gallery-card {{ background: white; border: 1px solid #d9dce2; border-radius: 12px; padding: 10px; }}
    .gallery-card img {{ width: 100%; border-radius: 8px; display: block; }}
    .links a {{ display: inline-block; margin-right: 12px; }}
  </style>
</head>
<body>
  <h1>PPT Creator Playground</h1>
  <p>Edit JSON, then validate, review, preview, or render using the local API. You can also bootstrap from workflow presets and inspect generated artifacts directly.</p>
  <div class='row'>
    <div>
      <label>Output PPTX path</label>
      <input id='outputPath' value='outputs/playground_output.pptx' />
    </div>
    <div>
      <label>Preview directory</label>
      <input id='previewDir' value='outputs/playground_previews' />
    </div>
  </div>
  <div class='row'>
    <div>
      <label>Workflow preset</label>
      <select id='workflowPreset'></select>
    </div>
    <div>
      <label>Template domain</label>
      <select id='templateDomain'></select>
    </div>
  </div>
  <div class='row'>
    <div>
      <label>Audience profile</label>
      <select id='audienceProfile'></select>
    </div>
    <div>
      <label>Preview backend</label>
      <select id='previewBackend'>
        <option value='auto'>auto</option>
        <option value='synthetic'>synthetic</option>
        <option value='office'>office</option>
      </select>
    </div>
    <div>
      <label>Baseline directory</label>
      <input id='baselineDir' value='' placeholder='optional baseline preview dir' />
    </div>
  </div>
  <textarea id='spec'>{initial_json}</textarea>
  <div class='toolbar'>
    <button onclick='loadWorkflow()'>Load workflow</button>
    <button onclick='loadTemplate()'>Load starter</button>
    <button onclick='runAction("/validate")'>Validate</button>
    <button onclick='runAction("/review")'>Review</button>
    <button onclick='runAction("/preview")'>Preview</button>
    <button onclick='runAction("/render")'>Render</button>
  </div>
  <div id='status' class='status'>Ready.</div>
  <div id='artifactLinks' class='links'></div>
  <pre id='result'>Ready.</pre>
  <div id='previewGallery' class='gallery'></div>
  <script>
    const storageKey = 'ppt_creator_playground_state_v3';

    function artifactUrl(path) {{
      return `/artifact?path=${{encodeURIComponent(path)}}`;
    }}

    function setStatus(message) {{
      document.getElementById('status').textContent = message;
    }}

    function collectState() {{
      return {{
        outputPath: document.getElementById('outputPath').value,
        previewDir: document.getElementById('previewDir').value,
        workflowPreset: document.getElementById('workflowPreset').value,
        templateDomain: document.getElementById('templateDomain').value,
        audienceProfile: document.getElementById('audienceProfile').value,
        previewBackend: document.getElementById('previewBackend').value,
        baselineDir: document.getElementById('baselineDir').value,
        spec: document.getElementById('spec').value,
      }};
    }}

    function persistState() {{
      localStorage.setItem(storageKey, JSON.stringify(collectState()));
    }}

    function restoreState() {{
      const raw = localStorage.getItem(storageKey);
      if (!raw) return;
      try {{
        const state = JSON.parse(raw);
        for (const [key, value] of Object.entries(state)) {{
          const element = document.getElementById(key);
          if (element && value !== undefined && value !== null) element.value = value;
        }}
      }} catch (_error) {{
        localStorage.removeItem(storageKey);
      }}
    }}

    function renderPreviewGallery(previews) {{
      const gallery = document.getElementById('previewGallery');
      gallery.innerHTML = '';
      for (const [index, preview] of previews.entries()) {{
        const card = document.createElement('div');
        card.className = 'gallery-card';
        card.innerHTML = `<img src="${{artifactUrl(preview)}}" alt="Preview ${{index + 1}}" /><div style="margin-top: 8px; font-size: 12px; color: #44576d;">Slide ${{String(index + 1).padStart(2, '0')}}</div>`;
        gallery.appendChild(card);
      }}
    }}

    function updateArtifactLinks(result) {{
      const links = [];
      if (result.output_path) links.push(`<a href="${{artifactUrl(result.output_path)}}">output</a>`);
      if (result.preview_result && result.preview_result.thumbnail_sheet) links.push(`<a href="${{artifactUrl(result.preview_result.thumbnail_sheet)}}">thumbnail sheet</a>`);
      document.getElementById('artifactLinks').innerHTML = links.join(' ');
    }}

    async function initControls() {{
      const templates = await fetch('/templates').then(r => r.json());
      const profiles = await fetch('/profiles').then(r => r.json());
      const workflows = await fetch('/workflows').then(r => r.json());
      const workflowSelect = document.getElementById('workflowPreset');
      const domainSelect = document.getElementById('templateDomain');
      const profileSelect = document.getElementById('audienceProfile');
      const workflowNone = document.createElement('option');
      workflowNone.value = '';
      workflowNone.textContent = '(none)';
      workflowSelect.appendChild(workflowNone);
      for (const workflow of workflows.workflows) {{
        const option = document.createElement('option');
        option.value = workflow.name;
        option.textContent = workflow.display_name;
        workflowSelect.appendChild(option);
      }}
      for (const domain of templates.domains) {{
        const option = document.createElement('option');
        option.value = domain;
        option.textContent = domain;
        domainSelect.appendChild(option);
      }}
      const none = document.createElement('option');
      none.value = '';
      none.textContent = '(none)';
      profileSelect.appendChild(none);
      for (const profile of profiles.profiles) {{
        const option = document.createElement('option');
        option.value = profile.display_name.toLowerCase();
        option.textContent = profile.display_name;
        profileSelect.appendChild(option);
      }}
      restoreState();
      for (const id of ['outputPath', 'previewDir', 'workflowPreset', 'templateDomain', 'audienceProfile', 'previewBackend', 'baselineDir', 'spec']) {{
        const element = document.getElementById(id);
        element.addEventListener('change', persistState);
        element.addEventListener('input', persistState);
      }}
    }}

    async function loadWorkflow() {{
      const workflowName = document.getElementById('workflowPreset').value;
      if (!workflowName) return;
      const response = await fetch('/workflow-template', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ workflow_name: workflowName }}),
      }});
      const data = await response.json();
      document.getElementById('spec').value = JSON.stringify(data.packet.template, null, 2);
      document.getElementById('templateDomain').value = data.packet.workflow.domain;
      document.getElementById('audienceProfile').value = data.packet.workflow.audience_profile;
      document.getElementById('previewBackend').value = data.packet.workflow.default_preview_backend;
      document.getElementById('outputPath').value = data.packet.workflow.default_output_pptx;
      document.getElementById('previewDir').value = data.packet.workflow.default_preview_dir;
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      setStatus(`Workflow loaded: ${{data.packet.workflow.display_name}}`);
      updateArtifactLinks({{}});
      renderPreviewGallery([]);
      persistState();
    }}

    async function loadTemplate() {{
      const domain = document.getElementById('templateDomain').value;
      const audienceProfile = document.getElementById('audienceProfile').value;
      const response = await fetch('/template', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ domain, audience_profile: audienceProfile || undefined }}),
      }});
      const data = await response.json();
      document.getElementById('spec').value = JSON.stringify(data.template, null, 2);
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      setStatus('Starter template loaded.');
      updateArtifactLinks({{}});
      renderPreviewGallery([]);
      persistState();
    }}

    async function runAction(path) {{
      const spec = JSON.parse(document.getElementById('spec').value);
      const outputPath = document.getElementById('outputPath').value;
      const previewDir = document.getElementById('previewDir').value;
      const previewBackend = document.getElementById('previewBackend').value;
      const baselineDir = document.getElementById('baselineDir').value;
      const payload = {{ spec }};
      if (path === '/render') {{
        payload.output_path = outputPath;
        payload.preview_output_dir = previewDir;
        payload.preview_backend = previewBackend;
        payload.preview_baseline_dir = baselineDir || undefined;
      }}
      if (path === '/preview') {{
        payload.output_dir = previewDir;
        payload.preview_backend = previewBackend;
        payload.baseline_dir = baselineDir || undefined;
      }}
      if (path === '/review') {{
        payload.preview_output_dir = previewDir;
        payload.preview_backend = previewBackend;
        payload.preview_baseline_dir = baselineDir || undefined;
      }}
      const response = await fetch(path, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload),
      }});
      const data = await response.json();
      document.getElementById('result').textContent = JSON.stringify(data, null, 2);
      const result = data.result || data;
      const previewPayload = result.preview_result || result;
      renderPreviewGallery(previewPayload.previews || []);
      updateArtifactLinks(result);
      setStatus(`Finished ${{path.replace('/', '')}} flow.`);
      persistState();
    }}
    initControls();
  </script>
</body>
</html>"""


def _resolve_service_asset_root(asset_root: str | Path | None) -> Path:
    return Path(asset_root or ".").resolve()


def _resolve_workspace_artifact_path(requested_path: str | Path) -> Path:
    workspace_root = Path(".").resolve()
    temp_root = Path(tempfile.gettempdir()).resolve()
    candidate = Path(requested_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (workspace_root / candidate).resolve()
    try:
        resolved.relative_to(workspace_root)
    except ValueError:
        try:
            resolved.relative_to(temp_root)
        except ValueError as exc:
            raise APIRequestError(
                "artifact path must stay inside the current workspace or the system temp directory",
                HTTPStatus.FORBIDDEN,
            ) from exc
    if not resolved.exists() or not resolved.is_file():
        raise APIRequestError(f"artifact not found: {resolved}", HTTPStatus.NOT_FOUND)
    return resolved


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
    include_review: bool = False,
    preview_output_dir: str | Path | None = None,
    preview_backend: str = "auto",
    preview_baseline_dir: str | Path | None = None,
    preview_write_diff_images: bool = False,
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
    quality_review = (
        review_presentation(
            spec,
            theme_name=effective_theme,
            asset_root=_resolve_service_asset_root(asset_root),
        )
        if include_review
        else None
    )
    preview_result: dict[str, object] | None = None
    preview_source: str | None = None

    if dry_run:
        if preview_output_dir:
            preview_result, preview_source = render_previews_for_rendered_artifact(
                spec,
                preview_output_dir,
                rendered_pptx=None,
                theme_name=effective_theme,
                asset_root=_resolve_service_asset_root(asset_root),
                primary_color=primary_color,
                secondary_color=secondary_color,
                basename=destination.stem,
                backend=preview_backend,
                baseline_dir=preview_baseline_dir,
                write_diff_images=preview_write_diff_images,
            )
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
            "quality_review": quality_review,
            "preview_output_dir": str(preview_output_dir) if preview_output_dir else None,
            "preview_source": preview_source,
            "preview_result": preview_result,
        }

    rendered_output = renderer.render(spec, destination)
    if preview_output_dir:
        preview_result, preview_source = render_previews_for_rendered_artifact(
            spec,
            preview_output_dir,
            rendered_pptx=rendered_output,
            theme_name=effective_theme,
            asset_root=_resolve_service_asset_root(asset_root),
            primary_color=primary_color,
            secondary_color=secondary_color,
            basename=destination.stem,
            backend=preview_backend,
            baseline_dir=preview_baseline_dir,
            write_diff_images=preview_write_diff_images,
        )
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
        "quality_review": quality_review,
        "preview_output_dir": str(preview_output_dir) if preview_output_dir else None,
        "preview_source": preview_source,
        "preview_result": preview_result,
    }


def review_spec_payload(
    spec_payload: dict[str, object],
    *,
    theme_name: str | None = None,
    asset_root: str | Path | None = None,
    preview_output_dir: str | Path | None = None,
    preview_backend: str = "auto",
    preview_baseline_dir: str | Path | None = None,
    preview_write_diff_images: bool = False,
) -> dict[str, object]:
    spec = PresentationInput.model_validate(spec_payload)
    review_result = review_presentation(
        spec,
        theme_name=theme_name or spec.presentation.theme,
        asset_root=_resolve_service_asset_root(asset_root),
    )
    preview_result: dict[str, object] | None = None
    preview_source: str | None = None
    if preview_output_dir:
        resolved_asset_root = _resolve_service_asset_root(asset_root)
        if preview_backend != "synthetic":
            with TemporaryDirectory(prefix="ppt_creator_api_review_preview_") as tmpdir:
                temp_pptx = Path(tmpdir) / "review-preview.pptx"
                PresentationRenderer(
                    theme_name=theme_name or spec.presentation.theme,
                    asset_root=resolved_asset_root,
                ).render(spec, temp_pptx)
                preview_result, preview_source = render_previews_for_rendered_artifact(
                    spec,
                    preview_output_dir,
                    rendered_pptx=temp_pptx,
                    theme_name=theme_name or spec.presentation.theme,
                    asset_root=resolved_asset_root,
                    basename="review-preview",
                    backend=preview_backend,
                    baseline_dir=preview_baseline_dir,
                    write_diff_images=preview_write_diff_images,
                )
        else:
            preview_result, preview_source = render_previews_for_rendered_artifact(
                spec,
                preview_output_dir,
                rendered_pptx=None,
                theme_name=theme_name or spec.presentation.theme,
                asset_root=resolved_asset_root,
                basename="review-preview",
                backend=preview_backend,
                baseline_dir=preview_baseline_dir,
                write_diff_images=preview_write_diff_images,
            )
        review_result = augment_review_with_preview_artifacts(review_result, preview_result)
    return {
        **review_result,
        "preview_output_dir": str(preview_output_dir) if preview_output_dir else None,
        "preview_source": preview_source,
        "preview_result": preview_result,
    }


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
    baseline_dir: str | Path | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
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
        baseline_dir=baseline_dir,
        diff_threshold=diff_threshold,
        write_diff_images=write_diff_images,
    )


def preview_pptx_payload(
    input_pptx: str | Path,
    *,
    output_dir: str | Path,
    theme_name: str | None = None,
    basename: str | None = None,
    baseline_dir: str | Path | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
) -> dict[str, object]:
    return render_previews_from_pptx(
        input_pptx,
        output_dir,
        theme_name=theme_name,
        basename=basename,
        baseline_dir=baseline_dir,
        diff_threshold=diff_threshold,
        write_diff_images=write_diff_images,
    )


def review_pptx_payload(
    input_pptx: str | Path,
    *,
    output_dir: str | Path,
    theme_name: str | None = None,
    basename: str | None = None,
    baseline_dir: str | Path | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
) -> dict[str, object]:
    return review_pptx_artifact(
        input_pptx,
        output_dir,
        theme_name=theme_name,
        basename=basename,
        baseline_dir=baseline_dir,
        diff_threshold=diff_threshold,
        write_diff_images=write_diff_images,
    )


def compare_pptx_payload(
    before_pptx: str | Path,
    after_pptx: str | Path,
    *,
    output_dir: str | Path,
    theme_name: str | None = None,
    basename: str | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
) -> dict[str, object]:
    return compare_pptx_artifacts(
        before_pptx,
        after_pptx,
        output_dir,
        theme_name=theme_name,
        basename=basename,
        diff_threshold=diff_threshold,
        write_diff_images=write_diff_images,
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

    def _html_response(self, status_code: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _binary_response(self, status_code: int, content_type: str, body: bytes) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
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
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json_response(HTTPStatus.OK, {"status": "ok"})
            return
        if parsed.path == "/playground":
            self._html_response(HTTPStatus.OK, _build_playground_html())
            return
        if parsed.path == "/profiles":
            self._json_response(
                HTTPStatus.OK,
                {"profiles": [get_audience_profile(name) for name in list_audience_profiles()]},
            )
            return
        if parsed.path == "/assets":
            self._json_response(
                HTTPStatus.OK,
                {"collections": [get_asset_collection(name) for name in list_asset_collections()]},
            )
            return
        if parsed.path == "/workflows":
            self._json_response(
                HTTPStatus.OK,
                {"workflows": [get_workflow_preset(name) for name in list_workflow_presets()]},
            )
            return
        if parsed.path == "/templates":
            self._json_response(HTTPStatus.OK, {"domains": list_template_domains()})
            return
        if parsed.path == "/artifact":
            query = parse_qs(parsed.query)
            requested_path = (query.get("path") or [""])[0]
            if not requested_path:
                self._json_response(HTTPStatus.BAD_REQUEST, {"error": "artifact path is required"})
                return
            artifact_path = _resolve_workspace_artifact_path(requested_path)
            content_type = mimetypes.guess_type(str(artifact_path))[0] or "application/octet-stream"
            self._binary_response(HTTPStatus.OK, content_type, artifact_path.read_bytes())
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
                    include_review=bool(payload.get("include_review", False)),
                    preview_output_dir=payload.get("preview_output_dir"),
                    preview_backend=str(payload["preview_backend"]) if payload.get("preview_backend") else "auto",
                    preview_baseline_dir=payload.get("preview_baseline_dir"),
                    preview_write_diff_images=bool(payload.get("preview_write_diff_images", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/review":
                spec_payload = _extract_spec_payload(payload)
                result = review_spec_payload(
                    spec_payload,
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    asset_root=payload.get("asset_root") or default_asset_root,
                    preview_output_dir=payload.get("preview_output_dir"),
                    preview_backend=str(payload["preview_backend"]) if payload.get("preview_backend") else "auto",
                    preview_baseline_dir=payload.get("preview_baseline_dir"),
                    preview_write_diff_images=bool(payload.get("preview_write_diff_images", False)),
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
                    baseline_dir=payload.get("baseline_dir"),
                    diff_threshold=float(payload.get("diff_threshold", 0.01)),
                    write_diff_images=bool(payload.get("write_diff_images", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/preview-pptx":
                if "input_pptx" not in payload:
                    raise APIRequestError("'input_pptx' is required for /preview-pptx")
                if "output_dir" not in payload:
                    raise APIRequestError("'output_dir' is required for /preview-pptx")
                result = preview_pptx_payload(
                    str(payload["input_pptx"]),
                    output_dir=str(payload["output_dir"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    basename=str(payload["basename"]) if payload.get("basename") else None,
                    baseline_dir=payload.get("baseline_dir"),
                    diff_threshold=float(payload.get("diff_threshold", 0.01)),
                    write_diff_images=bool(payload.get("write_diff_images", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/review-pptx":
                if "input_pptx" not in payload:
                    raise APIRequestError("'input_pptx' is required for /review-pptx")
                if "output_dir" not in payload:
                    raise APIRequestError("'output_dir' is required for /review-pptx")
                result = review_pptx_payload(
                    str(payload["input_pptx"]),
                    output_dir=str(payload["output_dir"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    basename=str(payload["basename"]) if payload.get("basename") else None,
                    baseline_dir=payload.get("baseline_dir"),
                    diff_threshold=float(payload.get("diff_threshold", 0.01)),
                    write_diff_images=bool(payload.get("write_diff_images", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/compare-pptx":
                if "before_pptx" not in payload:
                    raise APIRequestError("'before_pptx' is required for /compare-pptx")
                if "after_pptx" not in payload:
                    raise APIRequestError("'after_pptx' is required for /compare-pptx")
                if "output_dir" not in payload:
                    raise APIRequestError("'output_dir' is required for /compare-pptx")
                result = compare_pptx_payload(
                    str(payload["before_pptx"]),
                    str(payload["after_pptx"]),
                    output_dir=str(payload["output_dir"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    basename=str(payload["basename"]) if payload.get("basename") else None,
                    diff_threshold=float(payload.get("diff_threshold", 0.01)),
                    write_diff_images=bool(payload.get("write_diff_images", False)),
                )
                self._json_response(HTTPStatus.OK, {"result": result})
                return

            if self.path == "/template":
                if "domain" not in payload:
                    raise APIRequestError("'domain' is required for /template")
                template_payload = build_domain_template(
                    str(payload["domain"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                    audience_profile=str(payload["audience_profile"]) if payload.get("audience_profile") else None,
                )
                self._json_response(HTTPStatus.OK, {"template": template_payload})
                return

            if self.path == "/workflow-template":
                if "workflow_name" not in payload:
                    raise APIRequestError("'workflow_name' is required for /workflow-template")
                packet = build_workflow_packet(
                    str(payload["workflow_name"]),
                    theme_name=str(payload["theme_name"]) if payload.get("theme_name") else None,
                )
                self._json_response(HTTPStatus.OK, {"packet": packet})
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
