from __future__ import annotations

import argparse
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

    validate_parser = subparsers.add_parser("validate", help="Validate JSON without rendering")
    validate_parser.add_argument("input_json", help="Path to the structured JSON input")
    return parser


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


def format_validation_error(exc: ValidationError) -> list[str]:
    lines = ["Invalid presentation JSON."]
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", [])) or "input"
        lines.append(f"- {location}: {error.get('msg', 'validation error')}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            PresentationInput.from_path(args.input_json)
            print(f"[OK] Valid JSON: {args.input_json}")
            return 0

        spec = PresentationInput.from_path(args.input_json)
        asset_root = Path(args.asset_root).resolve() if args.asset_root else Path(args.input_json).resolve().parent
        renderer = PresentationRenderer(
            theme_name=args.theme or spec.presentation.theme,
            asset_root=asset_root,
        )
        output = renderer.render(spec, args.output_pptx)
        print(f"[OK] Generated deck: {output}")
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
