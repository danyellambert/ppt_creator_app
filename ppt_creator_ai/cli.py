from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from ppt_creator.qa import review_presentation
from ppt_creator.renderer import PresentationRenderer
from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
)
from ppt_creator_ai.providers import get_provider, list_provider_names
from ppt_creator_ai.refine import refine_presentation_input


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
    generate_parser.add_argument(
        "--review-json",
        help="Optional path to write a heuristic QA review for the generated deck JSON",
    )
    generate_parser.add_argument(
        "--render-pptx",
        help="Optional path to immediately render the generated deck into a .pptx file",
    )
    generate_parser.add_argument(
        "--asset-root",
        help="Optional asset root to use when rendering the generated deck or reviewing asset references",
    )
    generate_parser.add_argument(
        "--auto-refine",
        action="store_true",
        help="Run a heuristic refine pass on the generated deck when QA signals issues",
    )
    generate_parser.add_argument(
        "--refine-passes",
        type=int,
        default=1,
        help="Maximum number of heuristic refine passes to attempt when --auto-refine is enabled",
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
    review_json: str | Path | None = None,
    render_pptx: str | Path | None = None,
    asset_root: str | Path | None = None,
    auto_refine: bool = False,
    refine_passes: int = 1,
) -> dict[str, object]:
    input_path = Path(input_briefing)
    print_info(f"Loading briefing: {input_path}")
    briefing = BriefingInput.from_path(input_path)
    provider = get_provider(provider_name)
    print_info(f"Using provider: {provider.name}")
    result = provider.generate(briefing, theme_name=theme_name)
    payload = result.payload
    spec = PresentationInput.model_validate(payload)
    resolved_asset_root = Path(asset_root).resolve() if asset_root else input_path.parent.resolve()
    analysis_path: str | None = None
    analysis = result.analysis
    initial_deck_review = review_presentation(spec, asset_root=resolved_asset_root, theme_name=spec.presentation.theme)
    deck_review = initial_deck_review
    refinement_history: list[dict[str, object]] = []
    refine_applied = False

    if auto_refine:
        current_spec = spec
        current_review = initial_deck_review
        for pass_index in range(max(1, refine_passes)):
            if current_review["issue_count"] == 0:
                break
            candidate_spec = refine_presentation_input(current_spec, review=current_review)
            candidate_review = review_presentation(
                candidate_spec,
                asset_root=resolved_asset_root,
                theme_name=candidate_spec.presentation.theme,
            )
            refinement_history.append(
                {
                    "pass": pass_index + 1,
                    "before_issue_count": current_review["issue_count"],
                    "after_issue_count": candidate_review["issue_count"],
                    "before_average_score": current_review["average_score"],
                    "after_average_score": candidate_review["average_score"],
                }
            )
            payload_changed = candidate_spec.model_dump(mode="json") != current_spec.model_dump(mode="json")
            improved = (
                candidate_review["issue_count"] < current_review["issue_count"]
                or candidate_review["average_score"] > current_review["average_score"]
                or (
                    payload_changed
                    and candidate_review["issue_count"] <= current_review["issue_count"]
                    and candidate_review["average_score"] >= current_review["average_score"]
                )
            )
            if not improved:
                break
            current_spec = candidate_spec
            current_review = candidate_review
            refine_applied = True
        spec = current_spec
        deck_review = current_review

    payload = spec.model_dump(mode="json")
    output_path = write_json(output_json, payload)
    review_path: str | None = None
    rendered_pptx_path: str | None = None
    if analysis_json:
        analysis_output = write_json(
            analysis_json,
            {
                **analysis,
                "initial_generated_deck_review": initial_deck_review,
                "generated_deck_review": deck_review,
                "refinement_history": refinement_history,
            },
        )
        analysis_path = str(analysis_output)
    if review_json:
        review_output = write_json(review_json, deck_review)
        review_path = str(review_output)
    if render_pptx:
        renderer = PresentationRenderer(theme_name=spec.presentation.theme, asset_root=resolved_asset_root)
        rendered_output = renderer.render(spec, render_pptx)
        rendered_pptx_path = str(rendered_output)
        print_info(f"Rendered PPTX from generated deck: {rendered_output}")
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
        "review_output_json": review_path,
        "render_output_pptx": rendered_pptx_path,
        "auto_refine_enabled": auto_refine,
        "auto_refine_applied": refine_applied,
        "refine_passes_requested": refine_passes if auto_refine else 0,
        "refine_passes_completed": len(refinement_history),
        "image_suggestion_count": len(analysis["image_suggestions"]),
        "density_review_status": analysis["density_review"]["status"],
        "initial_generated_deck_review_status": initial_deck_review["status"],
        "initial_generated_deck_issue_count": initial_deck_review["issue_count"],
        "generated_deck_review_status": deck_review["status"],
        "generated_deck_issue_count": deck_review["issue_count"],
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
            review_json=args.review_json,
            render_pptx=args.render_pptx,
            asset_root=args.asset_root,
            auto_refine=args.auto_refine,
            refine_passes=args.refine_passes,
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
