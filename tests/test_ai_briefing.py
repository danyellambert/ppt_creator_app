from __future__ import annotations

import io
import json
from urllib import error

from ppt_creator.schema import PresentationInput
from ppt_creator_ai.briefing import (
    BriefingInput,
    assess_generated_payload_quality,
    build_briefing_analysis,
    build_briefing_from_intent_text,
    build_llm_generation_contract,
    build_minimal_briefing_from_intent_text,
    derive_briefing_freeform_signals,
    generate_presentation_input_from_briefing,
    generate_presentation_payload_from_briefing,
    suggest_slide_image_queries_from_briefing,
    summarize_text_to_executive_bullets,
)
from ppt_creator_ai.providers import get_provider, list_provider_names
from ppt_creator_ai.refine import refine_presentation_payload


def test_briefing_example_generates_valid_presentation_payload() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    payload = generate_presentation_payload_from_briefing(briefing)
    spec = PresentationInput.model_validate(payload)

    assert spec.presentation.title == briefing.title
    assert len(spec.slides) >= 6
    assert spec.slides[0].type.value == "title"
    assert any(slide.type.value == "agenda" for slide in spec.slides)
    assert any(slide.type.value == "summary" for slide in spec.slides)
    assert any(slide.type.value == "image_text" for slide in spec.slides)
    assert any(slide.type.value == "table" for slide in spec.slides)
    assert any(slide.type.value == "two_column" for slide in spec.slides)
    assert any(slide.type.value == "chart" for slide in spec.slides)


def test_briefing_generation_returns_presentation_input() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    spec = generate_presentation_input_from_briefing(briefing)

    assert isinstance(spec, PresentationInput)
    assert spec.presentation.client_name == "Acme Revenue Team"


def test_text_summarizer_builds_compact_executive_bullets() -> None:
    bullets = summarize_text_to_executive_bullets(
        "Teams are overloaded with repetitive work. Managers need better visibility into execution quality. The pilot should stay narrow before scaling.",
        max_bullets=3,
        max_words=8,
    )

    assert len(bullets) == 3
    assert bullets[0].startswith("Teams are overloaded")


def test_briefing_analysis_provides_image_suggestions_and_density_review() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    analysis = build_briefing_analysis(briefing)

    assert analysis["executive_summary_bullets"]
    assert analysis["image_suggestions"]
    assert analysis["slide_image_suggestions"]
    assert analysis["llm_generation_contract"]["response_rules"]["each_slide_requires_type"] is True
    assert analysis["density_review"]["status"] in {"ok", "review"}


def test_llm_generation_contract_exposes_supported_slide_types() -> None:
    contract = build_llm_generation_contract()

    assert contract["schema_version"] == "ppt_creator.presentation_input.v1"
    assert contract["response_rules"]["return_json_only"] is True
    assert contract["generation_preferences"]["prefer_rich_layout_mix_when_helpful"] is True
    assert contract["quality_guardrails"]["keep_output_language_consistent_with_briefing"] is True
    assert contract["quality_guardrails"]["avoid_renderer_scaffolding_or_placeholder_copy"] is True
    assert contract["quality_guardrails"]["prefer_narrative_archetype_consistency"] is True
    assert "decision" in contract["recommended_narrative_archetypes"]
    assert "section" in contract["supported_slide_types"]
    assert "cards" in contract["supported_slide_types"]
    assert "image_text" in contract["supported_slide_types"]
    assert "table" in contract["supported_slide_types"]
    assert "hero_cover" in contract["supported_slide_types"]["title"]["layout_variants"]


def test_slide_image_suggestions_are_granular_by_slide_type() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    suggestions = suggest_slide_image_queries_from_briefing(briefing)

    slide_types = {item["slide_type"] for item in suggestions}
    assert "title" in slide_types
    assert "metrics" in slide_types
    assert "timeline" in slide_types
    assert any(item["queries"] for item in suggestions)


def test_slide_image_suggestions_include_asset_style_and_focal_point_hints() -> None:
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    suggestions = suggest_slide_image_queries_from_briefing(briefing)

    assert suggestions
    for item in suggestions:
        assert item["asset_style"]
        assert item["composition_notes"]
        assert 0.0 <= item["focal_point"]["x"] <= 1.0
        assert 0.0 <= item["focal_point"]["y"] <= 1.0

    title_hint = next(item for item in suggestions if item["slide_type"] == "title")
    assert title_hint["focal_point"]["y"] < 0.5


def test_briefing_freeform_text_derives_content_signals() -> None:
    briefing = BriefingInput.model_validate(
        {
            "title": "AI copilots for sales teams",
            "briefing_text": (
                "Sales leaders are overloaded with repetitive preparation work and inconsistent storytelling. "
                "We should start with one workflow for leadership meeting prep, measure time saved and quality lift, and only then expand scope. "
                "The rollout should stay narrow in the first month and follow a milestone-based plan."
            ),
        }
    )

    derived = derive_briefing_freeform_signals(briefing)

    assert derived["objective"]
    assert derived["context"]
    assert derived["key_messages"]
    assert derived["recommendations"]
    assert derived["outline"]


def test_briefing_freeform_text_can_generate_valid_presentation() -> None:
    briefing = BriefingInput.model_validate(
        {
            "title": "AI copilots for sales teams",
            "briefing_text": (
                "Sales leaders are overloaded with repetitive preparation work and inconsistent storytelling. "
                "We should start with one workflow for leadership meeting prep, measure time saved and quality lift, and only then expand scope."
            ),
        }
    )

    spec = generate_presentation_input_from_briefing(briefing)

    assert isinstance(spec, PresentationInput)
    assert len(spec.slides) >= 4
    assert any(slide.type.value == "agenda" for slide in spec.slides)
    assert any(slide.type.value == "summary" for slide in spec.slides)


def test_intent_text_can_be_upconverted_to_briefing_input() -> None:
    briefing = build_briefing_from_intent_text(
        "Quero um deck para o board explicando por que devemos lançar um copiloto de vendas com visual premium, métricas, timeline, comparação de opções e um fechamento forte."
    )

    assert briefing.title
    assert briefing.briefing_text


def test_minimal_intent_briefing_keeps_raw_prompt_without_hardcoded_structure() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Quero uma apresentação para entrevista de AI Engineer mostrando minha trajetória, stack e projetos em IA."
    )

    assert briefing.title == "Entrevista de AI Engineer"
    assert briefing.briefing_text
    assert briefing.outline == []
    assert briefing.recommendations == []
    assert briefing.audience == "Hiring panel"
    assert briefing.objective


def test_minimal_intent_briefing_derives_better_title_for_board_prompt() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck para o board explicando por que devemos lançar um copiloto de vendas agora, com riscos, métricas e recomendação final."
    )

    assert briefing.title != "O board"
    assert "copiloto de vendas" in briefing.title.lower()


def test_minimal_intent_briefing_derives_compact_title_for_product_review_prompt() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Monte uma apresentação de product operating review mostrando onde o roadmap está diluído e qual a sequência recomendada para o próximo trimestre."
    )

    assert briefing.title == "Product operating review"


def test_intent_text_parser_extracts_interview_structure_more_intelligently() -> None:
    briefing = build_briefing_from_intent_text(
        """Quero uma apresentação para entrevista de AI Engineer mostrando minha trajetória, meus principais projetos em IA, minha capacidade de transformar problemas de negócio em soluções técnicas, e por que sou um candidato forte para a vaga.
        A apresentação deve ter visual premium, moderno e profissional, com storytelling claro, pouca poluição visual e foco em impacto.
        Inclua: apresentação pessoal, stack técnica, projetos mais relevantes, arquiteturas/fluxos de IA, resultados mensuráveis, forma de pensar em produção e escalabilidade, como trabalho com produto e negócio, e um fechamento forte mostrando o valor que posso gerar para a empresa.
        O tom deve ser confiante, sofisticado e objetivo, como alguém preparado para atuar em uma empresa exigente."""
    )

    assert briefing.title == "Entrevista de AI Engineer"
    assert briefing.audience == "Hiring panel"
    assert "Stack técnica" in briefing.outline
    assert "Arquiteturas e fluxos de IA" in briefing.outline
    assert "Produto e negócio" in briefing.outline
    assert "Valor que posso gerar" in briefing.outline
    assert not any(item.startswith("E ") for item in briefing.outline)
    assert any("premium" in item.lower() for item in briefing.recommendations)
    assert briefing.key_messages


def test_freeform_intent_generation_uses_richer_layout_mix() -> None:
    briefing = build_briefing_from_intent_text(
        "Quero um deck bonito para o board sobre um copiloto de vendas. Precisamos mostrar contexto, três benefícios executivos, métricas de impacto, uma timeline de rollout e um fechamento forte."
    )

    spec = generate_presentation_input_from_briefing(briefing)

    slide_types = {slide.type.value for slide in spec.slides}
    assert "section" in slide_types
    assert "cards" in slide_types


def test_board_intent_generation_uses_prompt_specific_localized_titles() -> None:
    briefing = build_briefing_from_intent_text(
        "Crie um deck para o board explicando por que devemos lançar um copiloto de vendas agora. Quero contexto executivo, métricas de impacto, trade-offs entre pilotar primeiro ou lançar já, riscos principais, roadmap de rollout, FAQ para objeções do board e fechamento forte."
    )

    payload = generate_presentation_payload_from_briefing(briefing)
    titles = [slide["title"] for slide in payload["slides"]]

    assert "Por que este movimento agora" in titles
    assert "O problema comercial que o copiloto resolve" in titles
    assert "Impacto esperado no funil" in titles
    assert "Riscos e objeções do board" in titles
    assert "Recomendação final ao board" in titles
    assert "Decisão recomendada" in titles
    assert "Situation overview" not in titles
    assert "Narrative frame" not in titles
    assert "Current context vs next move" not in titles
    assert "Action plan" not in titles


def test_quality_gate_flags_generic_payload_missing_prompt_requested_structure() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck para o board explicando por que devemos lançar um copiloto de vendas agora. Quero contexto executivo, métricas de impacto, trade-offs entre pilotar primeiro ou lançar já, riscos principais, roadmap de rollout, FAQ para objeções do board e fechamento forte."
    )

    payload = {
        "presentation": {
            "title": briefing.title,
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": briefing.title},
            {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
            {"type": "bullets", "title": "Situation overview", "bullets": ["Generic point"]},
            {"type": "summary", "title": "Executive summary", "bullets": ["Generic summary"]},
            {"type": "closing", "title": "Closing thought", "quote": "Generic close."},
        ],
    }

    quality = assess_generated_payload_quality(payload, briefing)

    assert quality["should_fallback"] is True
    assert "metrics" in quality["missing_required_types"]
    assert "timeline" in quality["missing_required_types"]
    assert "comparison" in quality["missing_required_types"]
    assert "faq" in quality["missing_required_types"]
    assert quality["placeholder_titles"]
    assert quality["specificity_score"] < quality["specificity_threshold"]
    assert any("generic placeholder titles" in problem for problem in quality["problems"])
    assert any("specificity score too low" in problem for problem in quality["problems"])


def test_quality_gate_flags_renderer_scaffolding_copy_and_weak_metrics() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck em português sobre uma iniciativa de IA com métricas, valor esperado e narrativa executiva forte."
    )

    payload = {
        "presentation": {
            "title": briefing.title,
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": briefing.title},
            {
                "type": "bullets",
                "title": "Narrativa principal",
                "body": "Executive lens",
                "bullets": ["What matters", "Specificidade", "Execução"],
            },
            {
                "type": "metrics",
                "title": "Impacto esperado",
                "metrics": [
                    {"label": "Eficiência", "value": "Alta"},
                    {"label": "Velocidade", "value": "Acelerada"},
                ],
            },
            {
                "type": "closing",
                "title": "Fechamento",
                "quote": "Candidate Name",
            },
            {"type": "summary", "title": "Síntese final", "bullets": ["Resumo"]},
        ],
    }

    quality = assess_generated_payload_quality(payload, briefing)

    assert quality["should_fallback"] is True
    assert quality["default_copy_leaks"]
    assert quality["weak_metric_values"]
    assert any("renderer/template scaffolding copy" in problem for problem in quality["problems"])
    assert any("weak qualitative values" in problem for problem in quality["problems"])


def test_quality_gate_flags_claims_without_enough_proof() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck em português defendendo uma iniciativa interna com narrativa forte e posicionamento convincente."
    )

    payload = {
        "presentation": {
            "title": briefing.title,
            "theme": "executive_premium_minimal",
        },
        "slides": [
            {"type": "title", "title": briefing.title},
            {
                "type": "bullets",
                "title": "Por que esta iniciativa é a melhor escolha",
                "body": "Temos alto impacto potencial e forte diferencial competitivo.",
                "bullets": [
                    "Maior valor estratégico para a organização",
                    "Capacidade end-to-end superior",
                    "Melhor escolha para acelerar resultado",
                ],
            },
            {"type": "summary", "title": "Síntese final", "bullets": ["Forte fit estratégico"]},
            {"type": "closing", "title": "Fechamento", "quote": "Somos a aposta certa."},
        ],
    }

    quality = assess_generated_payload_quality(payload, briefing)

    assert quality["should_fallback"] is True
    assert quality["claim_without_proof_slides"]
    assert any("strong claims appear without enough proof-bearing structure" in problem for problem in quality["problems"])


def test_quality_gate_accepts_summary_claim_when_nearby_evidence_slide_supports_it() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck para o board com métricas claras de impacto, comparação de opções e uma recomendação final forte."
    )

    payload = {
        "presentation": {"title": briefing.title, "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": briefing.title},
            {
                "type": "metrics",
                "title": "Impacto esperado",
                "metrics": [
                    {"label": "Win rate", "value": "31%"},
                    {"label": "Time saved", "value": "12h/mo"},
                ],
            },
            {
                "type": "summary",
                "title": "Recomendação final",
                "body": "Esta é a melhor escolha para acelerar resultado com menor risco.",
                "bullets": ["Maior impacto com rollout mais controlado"],
            },
            {"type": "closing", "title": "Fechamento", "quote": "A decisão recomendada equilibra valor e risco."},
        ],
    }

    quality = assess_generated_payload_quality(payload, briefing)

    assert quality["claim_without_proof_slides"] == []
    supported_summary = next(item for item in quality["claim_proof_relationships"] if item["slide_number"] == 3)
    assert supported_summary["supported"] is True
    assert supported_summary["relationship_type"] in {"self_proof", "adjacent_overlap", "summary_backlink"}


def test_quality_gate_exposes_dynamic_specificity_threshold_metadata() -> None:
    briefing = build_briefing_from_intent_text(
        "Monte um proposal deck para cliente explicando por que esta abordagem de IA é a melhor opção comercial, com diferenciais, riscos, métricas esperadas e plano de execução em fases."
    )

    payload = generate_presentation_payload_from_briefing(briefing)
    quality = assess_generated_payload_quality(payload, briefing)

    assert quality["structured_signal_count"] >= 3
    assert quality["specificity_threshold"] >= 24.0
    assert quality["specificity_score"] >= quality["specificity_threshold"]


def test_briefing_analysis_reports_broader_narrative_archetype() -> None:
    briefing = build_briefing_from_intent_text(
        "Monte um proposal deck para cliente explicando por que esta abordagem de IA é a melhor opção comercial, com diferenciais, riscos e plano de execução."
    )

    analysis = build_briefing_analysis(briefing)

    assert analysis["narrative_archetype"] == "proposal"


def test_prompt_driven_qa_smoke_for_multiple_archetypes() -> None:
    prompt_cases = [
        (
            "decision",
            "Quero um deck para o board explicando por que devemos lançar um copiloto de vendas agora, com métricas, comparação de opções, riscos e roadmap de rollout.",
            "decision",
        ),
        (
            "proposal",
            "Monte um proposal deck para cliente explicando por que esta abordagem de IA é a melhor opção comercial, com diferenciais, riscos e plano de execução.",
            "proposal",
        ),
        (
            "review",
            "Monte uma apresentação de product operating review mostrando onde o roadmap está diluído, quais decisões precisam ser tomadas, métricas, riscos, trade-offs e a sequência recomendada para o próximo trimestre.",
            "review",
        ),
        (
            "profile",
            "Quero uma apresentação para entrevista de AI Engineer mostrando minha trajetória, principais projetos em IA, profundidade técnica, produção e o valor que posso gerar para a empresa.",
            "profile",
        ),
        (
            "operating",
            "Crie um deck sobre como melhorar a operação de atendimento com IA, mostrando gargalos, métricas de execução, riscos, dependências e sequência operacional recomendada.",
            "operating",
        ),
    ]

    for _, prompt, expected_archetype in prompt_cases:
        briefing = build_briefing_from_intent_text(prompt)
        payload = generate_presentation_payload_from_briefing(briefing)
        quality = assess_generated_payload_quality(payload, briefing)

        assert quality["narrative_archetype"] == expected_archetype
        assert quality["specificity_score"] >= quality["specificity_threshold"]
        assert quality["should_fallback"] is False


def test_product_review_intent_derives_structured_signals_and_rich_slide_mix() -> None:
    briefing = build_briefing_from_intent_text(
        "Monte uma apresentação de product operating review mostrando onde o roadmap está diluído, quais decisões precisam ser tomadas, métricas, riscos, trade-offs e a sequência recomendada para o próximo trimestre."
    )

    assert len(briefing.metrics) == 3
    assert len(briefing.milestones) == 3
    assert len(briefing.options) == 2
    assert len(briefing.faqs) == 3

    payload = generate_presentation_payload_from_briefing(briefing)
    slide_types = {slide["type"] for slide in payload["slides"]}
    assert "metrics" in slide_types
    assert "chart" in slide_types
    assert "timeline" in slide_types
    assert "comparison" in slide_types
    assert "faq" in slide_types

    chart_slide = next(slide for slide in payload["slides"] if slide["type"] == "chart")
    assert any(value < 0 for value in chart_slide["chart_series"][0]["values"])


def test_interview_intent_generation_produces_better_candidate_story_titles() -> None:
    briefing = build_briefing_from_intent_text(
        """Quero uma apresentação para entrevista de AI Engineer mostrando minha trajetória, meus principais projetos em IA, minha capacidade de transformar problemas de negócio em soluções técnicas, e por que sou um candidato forte para a vaga.
        Inclua: apresentação pessoal, stack técnica, projetos mais relevantes, arquiteturas/fluxos de IA, resultados mensuráveis, forma de pensar em produção e escalabilidade, como trabalho com produto e negócio, e um fechamento forte mostrando o valor que posso gerar para a empresa."""
    )

    payload = generate_presentation_payload_from_briefing(briefing)
    slide_titles = [slide.get("title") for slide in payload["slides"]]

    assert "Por que sou um candidato forte para AI Engineer" in slide_titles
    assert "Stack técnica + visão de negócio" in slide_titles
    assert "O que cada capítulo prova" in slide_titles
    assert "O valor que posso gerar" in slide_titles


def test_provider_registry_exposes_supported_briefing_providers() -> None:
    assert list_provider_names() == ["heuristic", "local_service", "ollama_local"]
    assert get_provider("heuristic").name == "heuristic"
    assert get_provider("local_service").name == "local_service"
    assert get_provider("service").name == "local_service"
    assert get_provider("hf_local_llm_service").name == "local_service"
    assert get_provider("ollama_local").name == "ollama_local"
    assert get_provider("ollama").name == "ollama_local"


def test_ollama_local_provider_lists_available_models(monkeypatch) -> None:
    provider = get_provider("ollama_local")

    response_payload = {
        "models": [
            {"name": "qwen2.5:7b", "size": 123, "modified_at": "2026-04-03T10:00:00Z"},
            {"model": "llama3.2:3b", "size": 456, "modified_at": "2026-04-03T11:00:00Z"},
        ]
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    def _urlopen(req, *args, **kwargs):
        assert req.full_url.endswith("/api/tags")
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = provider.list_models()

    assert result["provider"] == "ollama_local"
    assert result["model_count"] == 2
    assert [item["name"] for item in result["models"]] == ["llama3.2:3b", "qwen2.5:7b"]


def test_local_service_provider_defaults_align_with_documented_service_defaults(monkeypatch) -> None:
    monkeypatch.delenv("PPT_CREATOR_AI_SERVICE_PROVIDER", raising=False)
    monkeypatch.delenv("PPT_CREATOR_AI_SERVICE_MODEL", raising=False)

    provider = get_provider("local_service")

    assert provider.resolve_provider_name() == "ollama"
    assert provider.resolve_provider_source() == "app_default"
    assert provider.resolve_model_name() == "nemotron-3-nano:30b-cloud"
    assert provider.resolve_model_source() == "app_default"


def test_local_service_provider_prefers_environment_over_app_defaults(monkeypatch) -> None:
    monkeypatch.setenv("PPT_CREATOR_AI_SERVICE_PROVIDER", "openai")
    monkeypatch.setenv("PPT_CREATOR_AI_SERVICE_MODEL", "gpt-4.1")

    provider = get_provider("local_service")

    assert provider.resolve_provider_name() == "openai"
    assert provider.resolve_provider_source() == "environment"
    assert provider.resolve_model_name() == "gpt-4.1"
    assert provider.resolve_model_source() == "environment"


def test_local_service_provider_surfaces_connection_error(monkeypatch) -> None:
    provider = get_provider("local_service")

    def _url_error(*args, **kwargs):
        raise error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _url_error)

    try:
        provider.generate(BriefingInput.from_path("examples/briefing_sales.json"))
    except RuntimeError as exc:
        assert "hf_local_llm_service" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError when hf_local_llm_service is unreachable")


def test_local_service_provider_normalizes_mocked_payload(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")

    response_payload = {
        "provider_name": "ollama",
        "payload": {
            "presentation": {
                "title": "AI copilots for sales teams",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {"type": "title", "title": "AI copilots for sales teams"},
                {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
                {"type": "closing", "title": "Closing", "quote": "Done."},
            ],
        },
        "analysis": {"provider": "ollama"},
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response())

    result = provider.generate(briefing)

    spec = PresentationInput.model_validate(result.payload)
    assert result.provider_name == "ollama"
    assert spec.presentation.title == "AI copilots for sales teams"


def test_local_service_provider_sends_generation_contract(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    captured: dict[str, object] = {}

    response_payload = {
        "provider_name": "ollama",
        "payload": {
            "presentation": {
                "title": "AI copilots for sales teams",
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {"type": "title", "title": "AI copilots for sales teams"},
                {"type": "closing", "title": "Closing", "quote": "Done."},
            ],
        },
        "analysis": {"provider": "ollama"},
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    def _urlopen(req, *args, **kwargs):
        captured.update(json.loads(req.data.decode("utf-8")))
        captured["url"] = req.full_url
        return _Response()

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = provider.generate(briefing)

    assert captured["url"].endswith(("/v1/generate", "/api/generate"))
    assert captured["provider_name"] == provider.resolve_provider_name()
    assert captured["model_name"] == provider.resolve_model_name()
    assert "Generation contract JSON" in str(captured["prompt"])
    assert '"each_slide_requires_type": true' in str(captured["prompt"]).lower()
    assert result.analysis["ai_exchange"]["transport"] == "local_service"
    assert result.analysis["ai_exchange"]["target_url"].endswith(("/v1/generate", "/api/generate"))
    assert result.analysis["ai_exchange"]["request_payload"]["model_name"] == provider.resolve_model_name()
    assert "Generation contract JSON" in str(result.analysis["ai_exchange"]["prompt"])
    assert result.analysis["ai_exchange"]["response_payload"]["provider_name"] == "ollama"


def test_local_service_provider_falls_back_from_low_quality_embedded_payload(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck para o board explicando por que devemos lançar um copiloto de vendas agora. Quero contexto executivo, métricas de impacto, trade-offs entre pilotar primeiro ou lançar já, riscos principais, roadmap de rollout, FAQ para objeções do board e fechamento forte."
    )

    response_payload = {
        "provider_name": "ollama",
        "payload": {
            "presentation": {
                "title": briefing.title,
                "theme": "executive_premium_minimal",
            },
            "slides": [
                {"type": "title", "title": briefing.title},
                {"type": "agenda", "title": "Agenda", "bullets": ["Context", "Decision"]},
                {"type": "bullets", "title": "Situation overview", "bullets": ["Generic point"]},
                {"type": "summary", "title": "Executive summary", "bullets": ["Generic summary"]},
                {"type": "closing", "title": "Closing thought", "quote": "Generic close."},
            ],
        },
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response())

    result = provider.generate(briefing)

    assert result.analysis["fallback_used"] is True
    assert "missing requested slide types" in str(result.analysis["fallback_reason"])
    generated_titles = [slide["title"] for slide in result.payload["slides"]]
    assert "Por que este movimento agora" in generated_titles
    assert "Riscos e objeções do board" in generated_titles


def test_local_service_provider_reports_repair_loop_when_retry_succeeds(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    captured_prompts: list[str] = []
    attempts = {"count": 0}

    valid_payload = generate_presentation_payload_from_briefing(briefing)

    class _Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

    def _urlopen(req, *args, **kwargs):
        payload = json.loads(req.data.decode("utf-8"))
        captured_prompts.append(str(payload.get("prompt") or ""))
        attempts["count"] += 1
        if attempts["count"] == 1:
            return _Response({"provider_name": "ollama", "response": '{"presentation": {"title": "Broken"}'})
        return _Response({"provider_name": "ollama", "payload": valid_payload})

    monkeypatch.setenv("PPT_CREATOR_AI_GENERATION_ATTEMPTS", "2")
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = provider.generate(briefing)

    assert attempts["count"] == 2
    assert result.analysis["repair_loop_used"] is True
    assert result.analysis["repair_attempt_count"] == 1
    assert any("Repair the previous invalid response" in prompt for prompt in captured_prompts[1:])


def test_refine_payload_rewrites_generic_titles_and_closing_copy_from_briefing() -> None:
    briefing = build_minimal_briefing_from_intent_text(
        "Crie um deck para o board explicando por que devemos lançar um copiloto de vendas agora, com riscos, métricas e recomendação final."
    )
    payload = {
        "presentation": {"title": briefing.title, "theme": "executive_premium_minimal"},
        "slides": [
            {"type": "title", "title": briefing.title},
            {"type": "summary", "title": "Executive summary", "body": "", "bullets": ["Resumo genérico"]},
            {"type": "closing", "title": "Closing", "quote": "Done."},
        ],
    }
    review = {
        "slides": [
            {"slide_number": 2, "risk_level": "high"},
            {"slide_number": 3, "risk_level": "high"},
        ]
    }

    refined = refine_presentation_payload(payload, review=review, briefing=briefing)

    assert refined["slides"][1]["title"] == "Recomendação final"
    assert refined["slides"][1]["body"]
    assert refined["slides"][2]["quote"] != "Done."


def test_local_service_provider_retries_retriable_http_errors(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    attempts = {"count": 0}

    response_payload = {
        "provider_name": "ollama",
        "payload": generate_presentation_payload_from_briefing(briefing),
        "analysis": {"provider": "ollama"},
    }

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(response_payload).encode("utf-8")

    def _urlopen(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            body = io.BytesIO(json.dumps({"error": {"message": "model busy", "code": "model_busy", "retriable": True}}).encode("utf-8"))
            raise error.HTTPError("http://127.0.0.1:8788/v1/generate", 503, "busy", hdrs=None, fp=body)
        return _Response()

    monkeypatch.setenv("PPT_CREATOR_AI_SERVICE_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("PPT_CREATOR_AI_SERVICE_RETRY_BACKOFF_SECONDS", "0")
    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = provider.generate(briefing)

    assert attempts["count"] == 3
    assert result.provider_name == "ollama"


def test_local_service_provider_surfaces_structured_http_error(monkeypatch) -> None:
    provider = get_provider("local_service")

    def _http_error(*args, **kwargs):
        body = io.BytesIO(json.dumps({"error": {"message": "model overloaded", "code": "model_busy", "retriable": False}}).encode("utf-8"))
        raise error.HTTPError("http://127.0.0.1:8788/v1/generate", 503, "busy", hdrs=None, fp=body)

    monkeypatch.setenv("PPT_CREATOR_AI_SERVICE_RETRY_ATTEMPTS", "1")
    monkeypatch.setattr("urllib.request.urlopen", _http_error)

    try:
        provider.generate(BriefingInput.from_path("examples/briefing_sales.json"))
    except RuntimeError as exc:
        message = str(exc)
        assert "HTTP 503" in message
        assert "model_busy" in message
        assert "retriable=false" in message
    else:
        raise AssertionError("Expected RuntimeError for structured HTTP error")


def test_local_service_provider_surfaces_structured_application_error(monkeypatch) -> None:
    provider = get_provider("local_service")

    class _Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps({"error": {"message": "upstream timeout", "code": "upstream_timeout", "retriable": False}}).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: _Response())

    try:
        provider.generate(BriefingInput.from_path("examples/briefing_sales.json"))
    except RuntimeError as exc:
        message = str(exc)
        assert "upstream timeout" in message
        assert "upstream_timeout" in message
        assert "retriable=false" in message
    else:
        raise AssertionError("Expected RuntimeError for structured application error payload")


def test_local_service_provider_falls_back_to_api_generate_when_v1_generate_is_missing(monkeypatch) -> None:
    provider = get_provider("local_service")
    briefing = BriefingInput.from_path("examples/briefing_sales.json")
    seen_urls: list[str] = []

    class _Response:
        def __init__(self, payload: dict[str, object]) -> None:
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self) -> bytes:
            return json.dumps(self._payload).encode("utf-8")

    def _urlopen(req, *args, **kwargs):
        seen_urls.append(req.full_url)
        if req.full_url.endswith("/v1/generate"):
            body = io.BytesIO(json.dumps({"error": "Route not found"}).encode("utf-8"))
            raise error.HTTPError(req.full_url, 404, "not found", hdrs=None, fp=body)
        return _Response(
            {
                "provider_name": "ollama",
                "model": "qwen2.5:7b",
                "response": json.dumps(
                    {
                        "presentation": {
                            "title": "AI copilots for sales teams",
                            "theme": "executive_premium_minimal",
                        },
                        "slides": [
                            {"type": "title", "title": "AI copilots for sales teams"},
                            {"type": "closing", "title": "Closing", "quote": "Done."},
                        ],
                    }
                ),
                "done": True,
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", _urlopen)

    result = provider.generate(briefing)

    assert seen_urls[0].endswith("/v1/generate")
    assert seen_urls[1].endswith("/api/generate")
    assert result.analysis["ai_exchange"]["target_url"].endswith("/api/generate")
    assert result.analysis["resolved_model"] == "qwen2.5:7b"
    assert result.payload["presentation"]["title"] == "AI copilots for sales teams"
