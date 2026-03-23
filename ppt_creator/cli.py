from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render structured JSON into a premium minimal PPTX deck.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a PPTX from a JSON file")
    render_parser.add_argument("input_json", help="Path to the structured JSON input")
    render_parser.add_argument("output_pptx", help="Destination .pptx path")
    render_parser.add_argument("--theme", help="Override the theme declared in the JSON")

    validate_parser = subparsers.add_parser("validate", help="Validate JSON without rendering")
    validate_parser.add_argument("input_json", help="Path to the structured JSON input")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        PresentationInput.from_path(args.input_json)
        print(f"[OK] Valid JSON: {args.input_json}")
        return 0

    spec = PresentationInput.from_path(args.input_json)
    renderer = PresentationRenderer(
        theme_name=args.theme or spec.presentation.theme,
        asset_root=Path(args.input_json).resolve().parent,
    )
    output = renderer.render(spec, args.output_pptx)
    print(f"[OK] Generated deck: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
