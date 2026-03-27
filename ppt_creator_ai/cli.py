from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ppt_creator_ai.briefing import (
    BriefingInput,
)
from ppt_creator_ai.providers import get_provider, list_provider_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate deck JSON from a structured briefing.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate presentation JSON from briefing JSON")
    generate_parser.add_argument("input_briefing", help="Path to the structured briefing JSON")
    generate_parser.add_argument("output_json", help="Destination deck JSON path")
    generate_parser.add_argument(
        "--provider",
        default="heuristic",
        choices=list_provider_names(),
        help="Provider used to transform briefing into deck JSON",
    )
    generate_parser.add_argument("--theme", help="Override the theme declared in the briefing")
    generate_parser.add_argument(
        "--analysis-json",
        help="Optional path to write a JSON analysis report with summary bullets, image suggestions, and density review",
    )
    generate_parser.add_argument("--report-json", help="Optional path to write a JSON generation report")

    providers_parser = subparsers.add_parser("providers", help="List available briefing providers")
    providers_parser.add_argument("--report-json", help="Optional path to write a JSON provider report")
    return parser


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


def print_info(message: str) -> None:
    print(f"[INFO] {message}")


def write_json(path: str | Path, payload: dict[str, object]) -> Path:
    output_path = Path(path)
    if output_path.suffix.lower() != ".json":
        raise ValueError(f"Output path must end with .json: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def generate_from_briefing(
    input_briefing: str | Path,
    output_json: str | Path,
    *,
    provider_name: str = "heuristic",
    theme_name: str | None = None,
    analysis_json: str | Path | None = None,
) -> dict[str, object]:
    input_path = Path(input_briefing)
    print_info(f"Loading briefing: {input_path}")
    briefing = BriefingInput.from_path(input_path)
    provider = get_provider(provider_name)
    print_info(f"Using provider: {provider.name}")
    result = provider.generate(briefing, theme_name=theme_name)
    payload = result.payload
    output_path = write_json(output_json, payload)
    analysis_path: str | None = None
    analysis = result.analysis
    if analysis_json:
        analysis_output = write_json(analysis_json, analysis)
        analysis_path = str(analysis_output)
    print(f"[OK] Generated deck JSON: {output_path} ({len(payload['slides'])} slides)")
    return {
        "mode": "briefing-generate",
        "provider": provider.name,
        "input_briefing": str(input_path),
        "output_json": str(output_path),
        "presentation_title": payload["presentation"]["title"],
        "theme": payload["presentation"]["theme"],
        "slide_count": len(payload["slides"]),
        "analysis_output_json": analysis_path,
        "image_suggestion_count": len(analysis["image_suggestions"]),
        "density_review_status": analysis["density_review"]["status"],
    }


def list_providers() -> dict[str, object]:
    providers = []
    for name in list_provider_names():
        provider = get_provider(name)
        providers.append({"name": provider.name, "description": provider.description})
    print_info(f"Available providers: {', '.join(item['name'] for item in providers)}")
    return {"mode": "briefing-providers", "providers": providers}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "providers":
            result = list_providers()
            if args.report_json:
                write_json(args.report_json, result)
            return 0

        result = generate_from_briefing(
            args.input_briefing,
            args.output_json,
            provider_name=args.provider,
            theme_name=args.theme,
            analysis_json=args.analysis_json,
        )
        if args.report_json:
            write_json(args.report_json, result)
        return 0
    except FileNotFoundError as exc:
        print_error(str(exc))
        return 2
    except ValidationError as exc:
        print_error(str(exc))
        return 2
    except ValueError as exc:
        print_error(str(exc))
        return 2
    except Exception as exc:
        print_error(f"Unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
