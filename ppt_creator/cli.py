from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


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
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate JSON without rendering")
    validate_parser.add_argument("input_json", help="Path to the structured JSON input")
    validate_parser.add_argument("--asset-root", help="Base directory for resolving relative image paths")
    validate_parser.add_argument(
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )
    validate_parser.add_argument("--report-json", help="Optional path to write a JSON validation report")

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
        "--check-assets",
        action="store_true",
        help="Warn when referenced image assets cannot be resolved",
    )
    return parser


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


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
    }


def validate_one(
    input_json: str | Path,
    *,
    asset_root: str | None = None,
    check_assets: bool = False,
) -> dict[str, object]:
    input_path = Path(input_json)
    spec = PresentationInput.from_path(input_path)
    theme_name = spec.presentation.theme
    missing_assets: list[str] = []

    if check_assets:
        renderer = PresentationRenderer(
            theme_name=theme_name,
            asset_root=resolve_asset_root(input_path, asset_root),
        )
        missing_assets = renderer.collect_missing_assets(spec)
        emit_missing_asset_warnings(missing_assets)

    print(f"[OK] Valid JSON: {input_path}")
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
) -> dict[str, object]:
    input_path = Path(input_json)
    spec = PresentationInput.from_path(input_path)
    effective_theme = theme_name or spec.presentation.theme
    renderer = PresentationRenderer(
        theme_name=effective_theme,
        asset_root=resolve_asset_root(input_path, asset_root),
        primary_color=primary_color,
        secondary_color=secondary_color,
    )
    output_path = renderer.validate_output_path(output_pptx)
    missing_assets = renderer.collect_missing_assets(spec)

    if check_assets and missing_assets:
        emit_missing_asset_warnings(missing_assets)

    if dry_run:
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
        )

    rendered_output = renderer.render(spec, output_path)
    print(f"[OK] Generated deck: {rendered_output}")
    return build_report(
        mode="render",
        input_path=input_path,
        spec=spec,
        output_path=rendered_output,
        theme_name=effective_theme,
        dry_run=False,
        rendered=True,
        missing_assets=missing_assets,
    )


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

        if args.command == "render-batch":
            input_root, input_paths = collect_batch_inputs(args.input_dir, args.pattern)
            output_root = Path(args.output_dir)
            results: list[dict[str, object]] = []

            for input_path in input_paths:
                relative_path = input_path.relative_to(input_root)
                output_path = output_root / relative_path.with_suffix(".pptx")
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
