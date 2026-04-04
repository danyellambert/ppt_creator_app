from __future__ import annotations

import json
from pathlib import Path

from ppt_creator.qa import review_presentation
from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import BriefingInput, build_llm_generation_contract
from ppt_creator_ai.providers import get_provider

BENCHMARK_SCENARIOS: list[dict[str, object]] = [
    {
        "name": "sales_qbr_prompt",
        "briefing": {
            "title": "Sales QBR turnaround",
            "audience": "Revenue leadership",
            "objective": "Tighten the operating rhythm and focus the quarter on higher-conviction deals.",
            "briefing_text": "Pipeline quality is uneven, managers are overloaded with deck preparation, and the quarter needs a narrower execution focus.",
            "metrics": [
                {"label": "Win rate", "value": "31%"},
                {"label": "Pipeline added", "value": "$8.4M"},
                {"label": "Plan attainment", "value": "104%"},
            ],
            "milestones": [
                {"title": "Reset forecast rules", "detail": "Clarify qualification rules and weekly governance.", "phase": "Month 1"},
                {"title": "Coach deal reviews", "detail": "Focus managers on conversion moments.", "phase": "Month 2"},
            ],
            "options": [
                {"title": "Keep current cadence", "body": "More activity, but limited quality improvement."},
                {"title": "Narrow the motion", "bullets": ["Tighter forecast hygiene", "Fewer priorities", "Stronger coaching"]},
            ],
            "faqs": [
                {"question": "What changes first?", "answer": "Forecast governance and deal review discipline."},
                {"question": "How do we measure it?", "answer": "Track conversion lift and slippage reduction."},
            ],
            "recommendations": [
                "Focus the quarter on fewer pipeline moves.",
                "Make forecast governance more explicit.",
                "Use manager coaching on high-value opportunities.",
            ],
        },
    },
    {
        "name": "board_strategy_prompt",
        "briefing": {
            "title": "Board strategy review",
            "audience": "Board of directors",
            "objective": "Turn strategic ambiguity into a clearer sequence of choices.",
            "briefing_text": "The company has too many simultaneous bets, weak sequencing, and recurring debates about where leadership focus should go first.",
            "metrics": [
                {"label": "Priority themes", "value": "5"},
                {"label": "Capital at risk", "value": "$12M"},
                {"label": "Execution score", "value": "68%"},
            ],
            "milestones": [
                {"title": "Diagnose", "detail": "Clarify the critical strategic questions.", "phase": "Q1"},
                {"title": "Decide", "detail": "Choose the explicit trade-offs.", "phase": "Q2"},
                {"title": "Sequence", "detail": "Stage execution deliberately.", "phase": "Q3"},
            ],
            "options": [
                {"title": "Broad portfolio", "body": "Retains optionality but increases management noise."},
                {"title": "Focused portfolio", "bullets": ["Sharper bets", "Better capital discipline", "Faster learning"]},
            ],
            "faqs": [
                {"question": "Why focus now?", "answer": "Because portfolio sprawl is already diluting execution quality."},
                {"question": "What does success look like?", "answer": "Fewer bets with clearer milestone accountability."},
            ],
            "recommendations": [
                "Reduce simultaneous strategic bets.",
                "Sequence investments against explicit milestones.",
                "Use board reviews to reinforce trade-off discipline.",
            ],
        },
    },
    {
        "name": "product_operating_prompt",
        "briefing": {
            "title": "Product operating review",
            "audience": "Product leadership",
            "objective": "Concentrate roadmap effort on the workflows with the strongest adoption pull.",
            "briefing_text": "The product roadmap is too parallel, adoption signals are mixed, and leadership needs a cleaner operating decision for the next quarter.",
            "metrics": [
                {"label": "Active teams", "value": "29"},
                {"label": "Release velocity", "value": "12"},
                {"label": "Adoption lift", "value": "18%"},
            ],
            "milestones": [
                {"title": "Protect core workflow", "detail": "Keep the strongest adoption motion healthy.", "phase": "Sprint 1"},
                {"title": "Pause low-conviction bets", "detail": "Reduce parallel roadmap load.", "phase": "Sprint 2"},
            ],
            "faqs": [
                {"question": "What moves first?", "answer": "The workflow with the strongest usage pull."},
                {"question": "What should wait?", "answer": "Initiatives without a clear adoption signal."},
            ],
            "recommendations": [
                "Concentrate roadmap scope.",
                "Use explicit decision gates.",
                "Tie expansion to adoption evidence.",
            ],
        },
    },
    {
        "name": "consulting_steerco_prompt",
        "briefing": {
            "title": "Consulting steerco",
            "audience": "Steering committee",
            "objective": "Reduce operating complexity before scaling the new model.",
            "briefing_text": "The program is absorbing too much complexity, ownership is unclear, and the steerco needs a cleaner recommendation with a practical action plan.",
            "metrics": [
                {"label": "Workstreams", "value": "7"},
                {"label": "Decision owners", "value": "3"},
                {"label": "Timeline slip", "value": "14%"},
            ],
            "options": [
                {"title": "Scale now", "body": "Keeps momentum but locks in complexity."},
                {"title": "Simplify first", "bullets": ["Clarify decisions", "Reduce scope", "Stabilize governance"]},
            ],
            "faqs": [
                {"question": "Why not scale now?", "answer": "The current model would scale unnecessary complexity."},
                {"question": "What unlocks scale later?", "answer": "Decision clarity and a narrower operating cadence."},
            ],
            "recommendations": [
                "Simplify the model before scaling.",
                "Clarify decision ownership.",
                "Use a staged operating plan.",
            ],
        },
    },
]


def run_generation_benchmark(
    output_dir: str | Path,
    *,
    provider_name: str = "heuristic",
    theme_name: str | None = None,
    write_json_decks: bool = False,
) -> dict[str, object]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    provider = get_provider(provider_name)
    asset_root = Path(".").resolve()

    results: list[dict[str, object]] = []
    unique_slide_types: set[str] = set()
    coverage: dict[str, int] = {}
    successful_generations = 0

    for scenario in BENCHMARK_SCENARIOS:
        scenario_name = str(scenario["name"])
        briefing = BriefingInput.model_validate(dict(scenario["briefing"]))
        try:
            generation = provider.generate(briefing, theme_name=theme_name)
            spec = PresentationInput.model_validate(generation.payload)
            review = review_presentation(spec, asset_root=asset_root, theme_name=spec.presentation.theme)
            slide_types = sorted({slide.type.value for slide in spec.slides})
            for slide_type in slide_types:
                unique_slide_types.add(slide_type)
                coverage[slide_type] = coverage.get(slide_type, 0) + 1

            deck_path = None
            if write_json_decks:
                deck_path = destination / f"{scenario_name}.json"
                deck_path.write_text(
                    json.dumps(spec.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

            results.append(
                {
                    "scenario": scenario_name,
                    "provider": generation.provider_name,
                    "valid": True,
                    "slide_count": len(spec.slides),
                    "review_status": review["status"],
                    "issue_count": review["issue_count"],
                    "average_score": review["average_score"],
                    "slide_types": slide_types,
                    "output_json": str(deck_path) if deck_path else None,
                }
            )
            successful_generations += 1
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "scenario": scenario_name,
                    "provider": provider.name,
                    "valid": False,
                    "error": str(exc),
                }
            )

    return {
        "mode": "briefing-benchmark",
        "provider": provider.name,
        "scenario_count": len(BENCHMARK_SCENARIOS),
        "successful_generations": successful_generations,
        "failed_generations": len(BENCHMARK_SCENARIOS) - successful_generations,
        "unique_slide_type_count": len(unique_slide_types),
        "unique_slide_types": sorted(unique_slide_types),
        "slide_type_coverage": dict(sorted(coverage.items())),
        "write_json_decks": write_json_decks,
        "generation_contract": build_llm_generation_contract(),
        "scenarios": results,
    }