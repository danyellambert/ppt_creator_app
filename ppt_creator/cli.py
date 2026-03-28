from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ppt_creator.preview import (
    render_previews,
    render_previews_for_rendered_artifact,
    render_previews_from_pptx,
)
from ppt_creator.qa import review_presentation
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput
from ppt_creator.templates import build_domain_template, list_template_domains


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render structured JSON into a premium minimal PPTX deck.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a PPTX from a JSON file")
    render_parser.add_argument("input_json", help="Path to the structured JSON input")
    render_parser.add_argument("output_pptx", help="Destination .pptx path")
    render_parser.add_argument("--theme", help="Override the theme declared in the JSON")
    render_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    render_parser.add_argument("--primary-color", help="Override the primary theme color with a 6-digit hex value")
    render_parser.add_argument(
        "--secondary-color",
        help="Override the secondary/accent theme color with a 6-digit hex value",
    )
    render_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the render plan without writing a .pptx file",
    )
    render_parser.add_argument("--report-json", help="Optional path to write a JSON render report")
    render_parser.add_argument(
        "--review",
        action="store_true",
        help="Include heuristic QA review summary in the render report",
    )
    render_parser.add_argument(
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )
    render_parser.add_argument(
        "--preview-dir",
        help="Optional directory to generate previews while rendering; when possible, this prefers previews from the final rendered .pptx",
    )
    render_parser.add_argument(
        "--preview-backend",
        choices=["auto", "synthetic", "office"],
        default="auto",
        help="Preview backend to use when --preview-dir is requested",
    )
    render_parser.add_argument(
        "--preview-baseline-dir",
        help="Optional baseline preview directory for visual regression when --preview-dir is used",
    )
    render_parser.add_argument(
        "--preview-write-diff-images",
        action="store_true",
        help="Write diff images when preview regression is enabled during render",
    )
    render_parser.add_argument(
        "--preview-report-json",
        help="Optional path to write a JSON preview report when --preview-dir is used",
    )

    preview_parser = subparsers.add_parser(
        "preview",
        help="Generate PNG slide previews and a thumbnail sheet from a JSON file",
    )
    preview_parser.add_argument("input_json", help="Path to the structured JSON input")
    preview_parser.add_argument("output_dir", help="Directory where PNG previews will be written")
    preview_parser.add_argument("--theme", help="Override the theme declared in the JSON")
    preview_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    preview_parser.add_argument("--primary-color", help="Override the primary theme color with a 6-digit hex value")
    preview_parser.add_argument(
        "--secondary-color",
        help="Override the secondary/accent theme color with a 6-digit hex value",
    )
    preview_parser.add_argument("--basename", help="Optional base name for generated preview files")
    preview_parser.add_argument(
        "--backend",
        choices=["auto", "synthetic", "office"],
        default="auto",
        help="Preview backend: synthetic Pillow renderer, office-based conversion, or auto fallback",
    )
    preview_parser.add_argument(
        "--debug-grid",
        action="store_true",
        help="Overlay layout guide lines on preview images",
    )
    preview_parser.add_argument(
        "--debug-safe-areas",
        action="store_true",
        help="Overlay safe-area bounds on preview images",
    )
    preview_parser.add_argument("--baseline-dir", help="Optional directory of golden preview PNGs for regression comparison")
    preview_parser.add_argument(
        "--diff-threshold",
        type=float,
        default=0.01,
        help="Threshold used to flag preview regressions against baseline images",
    )
    preview_parser.add_argument(
        "--write-diff-images",
        action="store_true",
        help="Write per-slide diff images when running baseline comparison",
    )
    preview_parser.add_argument("--report-json", help="Optional path to write a JSON preview report")

    preview_pptx_parser = subparsers.add_parser(
        "preview-pptx",
        help="Generate PNG previews directly from an existing .pptx file via the Office backend",
    )
    preview_pptx_parser.add_argument("input_pptx", help="Path to the input .pptx file")
    preview_pptx_parser.add_argument("output_dir", help="Directory where PNG previews will be written")
    preview_pptx_parser.add_argument("--theme", help="Optional theme used only for preview report/contact-sheet styling")
    preview_pptx_parser.add_argument("--basename", help="Optional base name for generated preview files")
    preview_pptx_parser.add_argument("--baseline-dir", help="Optional directory of golden preview PNGs for regression comparison")
    preview_pptx_parser.add_argument(
        "--diff-threshold",
        type=float,
        default=0.01,
        help="Threshold used to flag preview regressions against baseline images",
    )
    preview_pptx_parser.add_argument(
        "--write-diff-images",
        action="store_true",
        help="Write per-slide diff images when running baseline comparison",
    )
    preview_pptx_parser.add_argument("--report-json", help="Optional path to write a JSON PPTX preview report")

    validate_parser = subparsers.add_parser("validate", help="Validate JSON without rendering")
    validate_parser.add_argument("input_json", help="Path to the structured JSON input")
    validate_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    validate_parser.add_argument(
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )
    validate_parser.add_argument("--report-json", help="Optional path to write a JSON validation report")

    review_parser = subparsers.add_parser(
        "review",
        help="Run heuristic QA review for a presentation JSON",
    )
    review_parser.add_argument("input_json", help="Path to the structured JSON input")
    review_parser.add_argument("--theme", help="Override the theme declared in the JSON")
    review_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    review_parser.add_argument("--report-json", help="Optional path to write a JSON review report")

    template_parser = subparsers.add_parser(
        "template",
        help="Generate a starter JSON template for a deck domain",
    )
    template_parser.add_argument("domain", choices=list_template_domains(), help="Template domain to generate")
    template_parser.add_argument("output_json", help="Destination .json path")
    template_parser.add_argument("--theme", help="Override the default theme used by the template")

    batch_parser = subparsers.add_parser(
        "render-batch",
        help="Render all matching JSON files from a directory into an output directory",
    )
    batch_parser.add_argument("input_dir", help="Directory containing structured JSON files")
    batch_parser.add_argument("output_dir", help="Directory where rendered PPTX files will be created")
    batch_parser.add_argument("--pattern", default="*.json", help="Glob pattern for input files")
    batch_parser.add_argument("--theme", help="Override the theme declared in each JSON")
    batch_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    batch_parser.add_argument("--primary-color", help="Override the primary theme color with a 6-digit hex value")
    batch_parser.add_argument(
        "--secondary-color",
        help="Override the secondary/accent theme color with a 6-digit hex value",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the whole batch and preview outputs without writing PPTX files",
    )
    batch_parser.add_argument("--report-json", help="Optional path to write a JSON batch report")
    batch_parser.add_argument(
        "--review",
        action="store_true",
        help="Include heuristic QA review summaries for each rendered presentation",
    )
    batch_parser.add_argument(
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )
    return parser


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def print_info(message: str) -> None:
    print(f"[INFO] {message}")


def format_validation_error(exc: ValidationError) -> list[str]:
    lines = ["Invalid presentation JSON."]
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", [])) or "input"
        lines.append(f"- {location}: {error.get('msg', 'validation error')}")
    return lines


def resolve_asset_root(input_json: str | Path, asset_root: str | None) -> Path:
    input_path = Path(input_json).resolve()
    return Path(asset_root).resolve() if asset_root else input_path.parent


def emit_missing_asset_warnings(missing_assets: list[str]) -> None:
    for message in missing_assets:
        print_warning(message)


def write_report(path: str | Path, payload: dict[str, object]) -> None:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_json_payload(path: str | Path, payload: dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_json_output_path(output_json: str | Path) -> Path:
    destination = Path(output_json)
    if destination.suffix.lower() != ".json":
        raise ValueError(f"Template output path must end with .json: {destination}")
    return destination


def build_report(
    *,
    mode: str,
    input_path: Path,
    spec: PresentationInput,
    output_path: Path | None,
    theme_name: str,
    dry_run: bool,
    rendered: bool,
    missing_assets: list[str],
    quality_review: dict[str, object] | None = None,
    preview_output_dir: Path | None = None,
    preview_source: str | None = None,
    preview_result: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "mode": mode,
        "input_path": str(input_path),
        "output_path": str(output_path) if output_path else None,
        "presentation_title": spec.presentation.title,
        "theme": theme_name,
        "slide_count": len(spec.slides),
        "dry_run": dry_run,
        "rendered": rendered,
        "missing_asset_count": len(missing_assets),
        "missing_assets": missing_assets,
        "quality_review": quality_review,
        "preview_output_dir": str(preview_output_dir) if preview_output_dir else None,
        "preview_source": preview_source,
        "preview_result": preview_result,
    }


def build_preview_report(
    *,
    input_path: Path,
    spec: PresentationInput,
    output_dir: Path,
    theme_name: str,
    result: dict[str, object],
) -> dict[str, object]:
    return {
        "mode": "preview",
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "presentation_title": spec.presentation.title,
        "theme": theme_name,
        "slide_count": len(spec.slides),
        **result,
    }


def validate_one(
    input_json: str | Path,
    *,
    asset_root: str | None = None,
    check_assets: bool = False,
) -> dict[str, object]:
    input_path = Path(input_json)
    print_info(f"Loading input: {input_path}")
    spec = PresentationInput.from_path(input_path)
    theme_name = spec.presentation.theme
    print_info(f"Detected theme: {theme_name}")
    missing_assets: list[str] = []

    if check_assets:
        resolved_asset_root = resolve_asset_root(input_path, asset_root)
        print_info(f"Checking assets from: {resolved_asset_root}")
        renderer = PresentationRenderer(
            theme_name=theme_name,
            asset_root=resolved_asset_root,
        )
        missing_assets = renderer.collect_missing_assets(spec)
        emit_missing_asset_warnings(missing_assets)
        if not missing_assets:
            print_info("Asset check complete: no missing assets")

    print(f"[OK] Valid JSON: {input_path} ({len(spec.slides)} slides)")
    return build_report(
        mode="validate",
        input_path=input_path,
        spec=spec,
        output_path=None,
        theme_name=theme_name,
        dry_run=False,
        rendered=False,
        missing_assets=missing_assets,
    )


def review_one(
    input_json: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | None = None,
) -> dict[str, object]:
    input_path = Path(input_json)
    print_info(f"Loading input: {input_path}")
    spec = PresentationInput.from_path(input_path)
    resolved_asset_root = resolve_asset_root(input_path, asset_root)
    result = review_presentation(spec, asset_root=resolved_asset_root, theme_name=theme_name)
    print(
        f"[OK] Review completed: {result['issue_count']} issue(s), average score {result['average_score']}"
    )
    if result["overflow_risk_count"]:
        print_info(
            f"Overflow risk heuristics flagged {result['overflow_risk_count']} signal(s) across the deck"
        )
    if result["clipping_risk_count"]:
        print_info(
            f"Clipping risk heuristics flagged {result['clipping_risk_count']} signal(s) across the deck"
        )
    if result["balance_warning_count"]:
        print_info(
            f"Balance heuristics flagged {result['balance_warning_count']} signal(s) across the deck"
        )
    return {
        "input_path": str(input_path),
        **result,
    }


def render_one(
    input_json: str | Path,
    output_pptx: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    dry_run: bool = False,
    check_assets: bool = False,
    review: bool = False,
    preview_dir: str | Path | None = None,
    preview_backend: str = "auto",
    preview_baseline_dir: str | Path | None = None,
    preview_write_diff_images: bool = False,
    preview_report_json: str | Path | None = None,
) -> dict[str, object]:
    input_path = Path(input_json)
    print_info(f"Loading input: {input_path}")
    spec = PresentationInput.from_path(input_path)
    effective_theme = theme_name or spec.presentation.theme
    resolved_asset_root = resolve_asset_root(input_path, asset_root)
    print_info(f"Resolved theme: {effective_theme}")
    print_info(f"Asset root: {resolved_asset_root}")
    renderer = PresentationRenderer(
        theme_name=effective_theme,
        asset_root=resolved_asset_root,
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    output_path = renderer.validate_output_path(output_pptx)
    print_info(f"Planned output: {output_path}")
    missing_assets = renderer.collect_missing_assets(spec)
    preview_output_path = Path(preview_dir) if preview_dir else None
    quality_review = (
        review_presentation(spec, asset_root=resolved_asset_root, theme_name=effective_theme)
        if review
        else None
    )
    preview_result: dict[str, object] | None = None
    preview_source: str | None = None

    if check_assets and missing_assets:
        emit_missing_asset_warnings(missing_assets)
    elif check_assets:
        print_info("Asset check complete: no missing assets")

    if quality_review is not None:
        print_info(
            "QA review: "
            f"{quality_review['issue_count']} issue(s), average score {quality_review['average_score']}"
        )

    if dry_run:
        if preview_output_path:
            preview_result, preview_source = render_previews_for_rendered_artifact(
                spec,
                preview_output_path,
                rendered_pptx=None,
                theme_name=effective_theme,
                asset_root=resolved_asset_root,
                primary_color=primary_color,
                secondary_color=secondary_color,
                basename=output_path.stem,
                backend=preview_backend,
                baseline_dir=preview_baseline_dir,
                write_diff_images=preview_write_diff_images,
            )
            if preview_report_json:
                write_report(preview_report_json, preview_result)
        print(f"[OK] Dry run: {input_path} -> {output_path} ({len(spec.slides)} slides)")
        return build_report(
            mode="render",
            input_path=input_path,
            spec=spec,
            output_path=output_path,
            theme_name=effective_theme,
            dry_run=True,
            rendered=False,
            missing_assets=missing_assets,
            quality_review=quality_review,
            preview_output_dir=preview_output_path,
            preview_source=preview_source,
            preview_result=preview_result,
        )

    rendered_output = renderer.render(spec, output_path)
    if preview_output_path:
        preview_result, preview_source = render_previews_for_rendered_artifact(
            spec,
            preview_output_path,
            rendered_pptx=rendered_output,
            theme_name=effective_theme,
            asset_root=resolved_asset_root,
            primary_color=primary_color,
            secondary_color=secondary_color,
            basename=output_path.stem,
            backend=preview_backend,
            baseline_dir=preview_baseline_dir,
            write_diff_images=preview_write_diff_images,
        )
        if preview_report_json:
            write_report(preview_report_json, preview_result)
    print(f"[OK] Generated deck: {rendered_output} ({len(spec.slides)} slides)")
    return build_report(
        mode="render",
        input_path=input_path,
        spec=spec,
        output_path=rendered_output,
        theme_name=effective_theme,
        dry_run=False,
        rendered=True,
        missing_assets=missing_assets,
        quality_review=quality_review,
        preview_output_dir=preview_output_path,
        preview_source=preview_source,
        preview_result=preview_result,
    )


def preview_one(
    input_json: str | Path,
    output_dir: str | Path,
    *,
    theme_name: str | None = None,
    asset_root: str | None = None,
    primary_color: str | None = None,
    secondary_color: str | None = None,
    basename: str | None = None,
    debug_grid: bool = False,
    debug_safe_areas: bool = False,
    backend: str = "auto",
    baseline_dir: str | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
) -> dict[str, object]:
    input_path = Path(input_json)
    print_info(f"Loading input: {input_path}")
    spec = PresentationInput.from_path(input_path)
    effective_theme = theme_name or spec.presentation.theme
    resolved_asset_root = resolve_asset_root(input_path, asset_root)
    output_path = Path(output_dir)

    print_info(f"Resolved theme: {effective_theme}")
    print_info(f"Asset root: {resolved_asset_root}")
    print_info(f"Preview output directory: {output_path}")

    result = render_previews(
        spec,
        output_path,
        theme_name=effective_theme,
        asset_root=resolved_asset_root,
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
    print(
        f"[OK] Generated previews: {result['preview_count']} slide image(s) + thumbnail sheet"
    )
    if result["quality_review"]["warning_count"]:
        print_info(
            f"Preview quality review flagged {result['quality_review']['warning_count']} issue(s)"
        )
    if result["preview_artifact_review"]["status"] != "ok":
        print_info(
            "Preview artifact review: "
            f"{result['preview_artifact_review']['edge_contact_count']} edge-contact signal(s), "
            f"{result['preview_artifact_review']['edge_density_warning_count']} edge-density signal(s)"
        )
    if result["visual_regression"] is not None:
        print_info(
            "Preview regression check: "
            f"{result['visual_regression']['diff_count']} diff(s), "
            f"{result['visual_regression']['missing_baseline_count']} missing baseline(s)"
        )
    return build_preview_report(
        input_path=input_path,
        spec=spec,
        output_dir=output_path,
        theme_name=effective_theme,
        result=result,
    )


def preview_pptx_one(
    input_pptx: str | Path,
    output_dir: str | Path,
    *,
    theme_name: str | None = None,
    basename: str | None = None,
    baseline_dir: str | None = None,
    diff_threshold: float = 0.01,
    write_diff_images: bool = False,
) -> dict[str, object]:
    input_path = Path(input_pptx)
    output_path = Path(output_dir)
    print_info(f"Loading PPTX input: {input_path}")
    print_info(f"Preview output directory: {output_path}")
    result = render_previews_from_pptx(
        input_path,
        output_path,
        theme_name=theme_name,
        basename=basename,
        baseline_dir=baseline_dir,
        diff_threshold=diff_threshold,
        write_diff_images=write_diff_images,
    )
    print(f"[OK] Generated PPTX previews: {result['preview_count']} slide image(s) + thumbnail sheet")
    if result["preview_artifact_review"]["status"] != "ok":
        print_info(
            "PPTX preview artifact review: "
            f"{result['preview_artifact_review']['edge_contact_count']} edge-contact signal(s), "
            f"{result['preview_artifact_review']['edge_density_warning_count']} edge-density signal(s)"
        )
    if result["visual_regression"] is not None:
        print_info(
            "PPTX preview regression check: "
            f"{result['visual_regression']['diff_count']} diff(s), "
            f"{result['visual_regression']['missing_baseline_count']} missing baseline(s)"
        )
    return result


def collect_batch_inputs(input_dir: str | Path, pattern: str) -> tuple[Path, list[Path]]:
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Input directory must be a directory: {root}")

    input_paths = sorted(path for path in root.glob(pattern) if path.is_file())
    if not input_paths:
        raise FileNotFoundError(f"No JSON files matched pattern '{pattern}' in: {root}")
    return root, input_paths


def generate_template(
    domain: str,
    output_json: str | Path,
    *,
    theme_name: str | None = None,
) -> dict[str, object]:
    output_path = validate_json_output_path(output_json)
    print_info(f"Generating template for domain: {domain}")
    payload = build_domain_template(domain, theme_name=theme_name)
    write_json_payload(output_path, payload)
    print(f"[OK] Generated template: {output_path} ({len(payload['slides'])} slides)")
    return {
        "mode": "template",
        "domain": domain,
        "output_path": str(output_path),
        "theme": payload["presentation"]["theme"],
        "slide_count": len(payload["slides"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            report = validate_one(
                args.input_json,
                asset_root=args.asset_root,
                check_assets=args.check_assets,
            )
            if args.report_json:
                write_report(args.report_json, report)
            return 0

        if args.command == "review":
            report = review_one(
                args.input_json,
                theme_name=args.theme,
                asset_root=args.asset_root,
            )
            if args.report_json:
                write_report(args.report_json, report)
            return 0

        if args.command == "preview":
            report = preview_one(
                args.input_json,
                args.output_dir,
                theme_name=args.theme,
                asset_root=args.asset_root,
                primary_color=args.primary_color,
                secondary_color=args.secondary_color,
                basename=args.basename,
                debug_grid=args.debug_grid,
                debug_safe_areas=args.debug_safe_areas,
                backend=args.backend,
                baseline_dir=args.baseline_dir,
                diff_threshold=args.diff_threshold,
                write_diff_images=args.write_diff_images,
            )
            if args.report_json:
                write_report(args.report_json, report)
            return 0

        if args.command == "preview-pptx":
            report = preview_pptx_one(
                args.input_pptx,
                args.output_dir,
                theme_name=args.theme,
                basename=args.basename,
                baseline_dir=args.baseline_dir,
                diff_threshold=args.diff_threshold,
                write_diff_images=args.write_diff_images,
            )
            if args.report_json:
                write_report(args.report_json, report)
            return 0

        if args.command == "template":
            generate_template(args.domain, args.output_json, theme_name=args.theme)
            return 0

        if args.command == "render-batch":
            input_root, input_paths = collect_batch_inputs(args.input_dir, args.pattern)
            output_root = Path(args.output_dir)
            print_info(f"Batch input directory: {input_root}")
            print_info(f"Batch output directory: {output_root}")
            print_info(f"Matched files: {len(input_paths)}")
            results: list[dict[str, object]] = []

            for batch_index, input_path in enumerate(input_paths, start=1):
                relative_path = input_path.relative_to(input_root)
                output_path = output_root / relative_path.with_suffix(".pptx")
                print_info(f"[{batch_index}/{len(input_paths)}] Processing {input_path.name}")
                results.append(
                    render_one(
                        input_path,
                        output_path,
                        theme_name=args.theme,
                        asset_root=args.asset_root,
                        primary_color=args.primary_color,
                        secondary_color=args.secondary_color,
                        dry_run=args.dry_run,
                        check_assets=args.check_assets,
                        review=args.review,
                    )
                )

            batch_report = {
                "mode": "render-batch",
                "input_dir": str(input_root),
                "output_dir": str(output_root),
                "pattern": args.pattern,
                "count": len(results),
                "rendered_count": sum(1 for result in results if result["rendered"]),
                "dry_run": args.dry_run,
                "missing_asset_count": sum(int(result["missing_asset_count"]) for result in results),
                "review_enabled": args.review,
                "review_average_score": int(
                    sum(
                        int(result["quality_review"]["average_score"])
                        for result in results
                        if result["quality_review"] is not None
                    )
                    / max(1, sum(1 for result in results if result["quality_review"] is not None))
                )
                if args.review
                else None,
                "review_overflow_risk_count": sum(
                    int(result["quality_review"]["overflow_risk_count"])
                    for result in results
                    if result["quality_review"] is not None
                )
                if args.review
                else None,
                "review_clipping_risk_count": sum(
                    int(result["quality_review"]["clipping_risk_count"])
                    for result in results
                    if result["quality_review"] is not None
                )
                if args.review
                else None,
                "review_balance_warning_count": sum(
                    int(result["quality_review"]["balance_warning_count"])
                    for result in results
                    if result["quality_review"] is not None
                )
                if args.review
                else None,
                "results": results,
            }
            if args.report_json:
                write_report(args.report_json, batch_report)

            if args.dry_run:
                print(f"[OK] Batch dry run completed: {len(results)} presentation(s)")
            else:
                print(f"[OK] Batch render completed: {len(results)} presentation(s)")
            return 0

        report = render_one(
            args.input_json,
            args.output_pptx,
            theme_name=args.theme,
            asset_root=args.asset_root,
            primary_color=args.primary_color,
            secondary_color=args.secondary_color,
            dry_run=args.dry_run,
            check_assets=args.check_assets,
            review=args.review,
            preview_dir=args.preview_dir,
            preview_backend=args.preview_backend,
            preview_baseline_dir=args.preview_baseline_dir,
            preview_write_diff_images=args.preview_write_diff_images,
            preview_report_json=args.preview_report_json,
        )
        if args.report_json:
            write_report(args.report_json, report)
        return 0
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 2
    except ValidationError as exc:
        for line in format_validation_error(exc):
            print_error(line)
        return 2
    except ValueError as exc:
        print_error(str(exc))
        return 2
    except Exception as exc:
        print_error(f"Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
