from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ppt_creator.schema import PresentationInput


def _clean_optional_text(value: object) -> str | None | object:
    if value is None or not isinstance(value, str):
        return value
    cleaned = value.strip()
    return cleaned or None


def _clean_required_text(value: object, field_name: str) -> str | object:
    if not isinstance(value, str):
        return value
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def _clean_string_list(values: list[str], *, field_name: str) -> list[str]:
    cleaned: list[str] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, str):
            raise ValueError(f"{field_name} #{index} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} #{index} cannot be empty")
        cleaned.append(normalized)
    return cleaned


def _shorten_words(value: str | None, *, max_words: int) -> str | None:
    if not value:
        return value
    words = value.split()
    if len(words) <= max_words:
        return value.strip()
    return " ".join(words[:max_words]).rstrip(" ,;:.!?") + "..."


def _split_sentences(text: str | None) -> list[str]:
    if not text:
        return []
    return [segment.strip() for segment in re.split(r"[\n\.\?!;]+", text) if segment.strip()]


def _sentence_case(value: str | None) -> str | None:
    if not value:
        return value
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[0].upper() + cleaned[1:]


def _infer_prompt_language(text: str | None) -> str:
    normalized = f" {(text or '').lower()} "
    if any(char in normalized for char in "ãõçáéíóúâêôà"):
        return "pt"

    portuguese_markers = [
        " quero ",
        " apresentação ",
        " apresentacao ",
        " vaga ",
        " recrutador ",
        " lideran",
        " métricas ",
        " metricas ",
        " roteiro ",
        " riscos ",
        " negócio ",
        " negocio ",
        " próximo trimestre ",
        " proximo trimestre ",
        " por que ",
        " devemos ",
    ]
    score = sum(1 for marker in portuguese_markers if marker in normalized)
    return "pt" if score >= 2 else "en"


def _condense_messages(values: list[str], *, max_items: int, max_words: int) -> list[str]:
    condensed: list[str] = []
    for value in values:
        shortened = _shorten_words(_sentence_case(value), max_words=max_words)
        if shortened and shortened not in condensed:
            condensed.append(shortened)
        if len(condensed) >= max_items:
            break
    return condensed


def _localized_phrase(language: str, *, pt: str, en: str) -> str:
    return pt if language == "pt" else en


_SPECIFICITY_STOPWORDS = {
    "about",
    "above",
    "across",
    "after",
    "agora",
    "algo",
    "ainda",
    "also",
    "apenas",
    "apresentacao",
    "apresentação",
    "approach",
    "assim",
    "between",
    "briefing",
    "clearly",
    "como",
    "contra",
    "deck",
    "decks",
    "dentro",
    "depois",
    "desde",
    "dessa",
    "desse",
    "deste",
    "diferente",
    "disso",
    "each",
    "esse",
    "esta",
    "este",
    "executive",
    "fazer",
    "final",
    "forte",
    "forma",
    "from",
    "geral",
    "have",
    "isso",
    "logo",
    "mais",
    "mesmo",
    "muito",
    "narrativa",
    "need",
    "objetiva",
    "objetivo",
    "only",
    "para",
    "pela",
    "pelos",
    "pelo",
    "porque",
    "porquê",
    "premium",
    "quero",
    "role",
    "should",
    "slide",
    "slides",
    "sobre",
    "strong",
    "tech",
    "technological",
    "tecnologico",
    "tecnológico",
    "that",
    "them",
    "this",
    "through",
    "uma",
    "with",
}


def _extract_keyword_tokens(text: str | None, *, min_length: int = 4) -> list[str]:
    if not text:
        return []
    tokens: list[str] = []
    for token in re.findall(r"[A-Za-zÀ-ÿ0-9_+-]+", text.lower()):
        cleaned = token.strip("_+-")
        if len(cleaned) < min_length:
            continue
        if cleaned.isdigit() or cleaned in _SPECIFICITY_STOPWORDS:
            continue
        tokens.append(cleaned)
    return tokens


def _infer_narrative_archetype(intent_text: str | None) -> str:
    lowered = (intent_text or "").lower()
    scores = {
        "decision": 0,
        "review": 0,
        "strategy": 0,
        "profile": 0,
        "proposal": 0,
        "operating": 0,
    }

    def add_score(archetype: str, keywords: list[str], *, weight: int) -> None:
        for keyword in keywords:
            if keyword in lowered:
                scores[archetype] += weight

    add_score("profile", ["entrevista", "interview", "candidate", "candidato", "vaga", "hiring"], weight=5)
    add_score("review", ["qbr", "review", "operating review", "status update", "retrospective", "business review"], weight=4)
    add_score("proposal", ["proposal", "proposta", "pitch", "rfp", "cliente", "commercial proposal", "business case"], weight=4)
    add_score("strategy", ["strategy", "estratég", "north star", "vision", "visioning", "positioning", "strategic"], weight=4)
    add_score(
        "operating",
        [
            "operating",
            "operation",
            "operação",
            "operacao",
            "operacional",
            "workflow",
            "process",
            "processo",
            "governance",
            "roadmap",
            "rollout",
            "execution model",
            "gargalos",
            "bottleneck",
            "dependências",
            "dependencias",
            "sequência operacional",
            "sequencia operacional",
        ],
        weight=2,
    )
    add_score(
        "decision",
        [
            "por que",
            "why",
            "recommend",
            "recomendação",
            "recomendacao",
            "decision",
            "launch",
            "lançar",
            "lancar",
            "trade-off",
            "tradeoff",
            "go/no-go",
            "options",
            "opções",
            "opcoes",
            "melhor escolha",
            "best choice",
            "devemos",
        ],
        weight=3,
    )

    priority = ["profile", "proposal", "review", "strategy", "operating", "decision"]
    best = max(scores.values())
    if best <= 0:
        return "decision"
    for archetype in priority:
        if scores[archetype] == best:
            return archetype
    return "decision"


def _default_outline_for_prompt(*, language: str, domain: str, candidate_story_mode: bool, narrative_archetype: str) -> list[str]:
    if candidate_story_mode:
        return [
            _localized_phrase(language, pt="Quem sou e como penso", en="Who I am and how I think"),
            _localized_phrase(language, pt="Projetos relevantes", en="Relevant projects"),
            _localized_phrase(language, pt="Stack e arquitetura de IA", en="AI stack and architecture"),
            _localized_phrase(language, pt="Produção e escalabilidade", en="Production and scalability"),
            _localized_phrase(language, pt="Produto e negócio", en="Product and business"),
            _localized_phrase(language, pt="Valor para a empresa", en="Value to the company"),
        ]
    if domain == "sales":
        return [
            _localized_phrase(language, pt="Tese de lançamento", en="Launch thesis"),
            _localized_phrase(language, pt="Impacto esperado", en="Expected impact"),
            _localized_phrase(language, pt="Roteiro de rollout", en="Rollout roadmap"),
            _localized_phrase(language, pt="Trade-offs da decisão", en="Decision trade-offs"),
            _localized_phrase(language, pt="Riscos e objeções", en="Risks and objections"),
            _localized_phrase(language, pt="Recomendação final", en="Final recommendation"),
        ]
    if domain == "product":
        return [
            _localized_phrase(language, pt="Diagnóstico do roadmap", en="Roadmap diagnosis"),
            _localized_phrase(language, pt="KPIs críticos", en="Critical KPIs"),
            _localized_phrase(language, pt="Sequência do trimestre", en="Quarter sequence"),
            _localized_phrase(language, pt="Trade-offs de foco", en="Focus trade-offs"),
            _localized_phrase(language, pt="Riscos da mudança", en="Change risks"),
            _localized_phrase(language, pt="Recomendação do review", en="Review recommendation"),
        ]
    if domain == "board":
        return [
            _localized_phrase(language, pt="Contexto da decisão", en="Decision context"),
            _localized_phrase(language, pt="Sinais principais", en="Key signals"),
            _localized_phrase(language, pt="Opções em jogo", en="Options in play"),
            _localized_phrase(language, pt="Riscos e mitigação", en="Risks and mitigation"),
            _localized_phrase(language, pt="Próximos passos", en="Next steps"),
            _localized_phrase(language, pt="Recomendação final", en="Final recommendation"),
        ]
    if narrative_archetype == "review":
        return [
            _localized_phrase(language, pt="Diagnóstico atual", en="Current diagnosis"),
            _localized_phrase(language, pt="Sinais principais", en="Key signals"),
            _localized_phrase(language, pt="O que está funcionando", en="What is working"),
            _localized_phrase(language, pt="O que precisa corrigir", en="What needs correction"),
            _localized_phrase(language, pt="Riscos e decisões", en="Risks and decisions"),
            _localized_phrase(language, pt="Próximos passos", en="Next steps"),
        ]
    if narrative_archetype == "proposal":
        return [
            _localized_phrase(language, pt="Tese da proposta", en="Proposal thesis"),
            _localized_phrase(language, pt="Por que esta abordagem", en="Why this approach"),
            _localized_phrase(language, pt="Provas e diferenciais", en="Proof and differentiators"),
            _localized_phrase(language, pt="Escopo e execução", en="Scope and execution"),
            _localized_phrase(language, pt="Riscos e mitigação", en="Risks and mitigation"),
            _localized_phrase(language, pt="Recomendação comercial", en="Commercial recommendation"),
        ]
    if narrative_archetype == "strategy":
        return [
            _localized_phrase(language, pt="Tese estratégica", en="Strategic thesis"),
            _localized_phrase(language, pt="Mudança de contexto", en="Context shift"),
            _localized_phrase(language, pt="Opções e trade-offs", en="Options and trade-offs"),
            _localized_phrase(language, pt="Aposta recomendada", en="Recommended bet"),
            _localized_phrase(language, pt="Riscos e alavancas", en="Risks and levers"),
            _localized_phrase(language, pt="Próximos passos", en="Next steps"),
        ]
    if narrative_archetype == "operating":
        return [
            _localized_phrase(language, pt="Diagnóstico operacional", en="Operating diagnosis"),
            _localized_phrase(language, pt="Gargalos principais", en="Main bottlenecks"),
            _localized_phrase(language, pt="Sequência recomendada", en="Recommended sequence"),
            _localized_phrase(language, pt="Riscos e dependências", en="Risks and dependencies"),
            _localized_phrase(language, pt="Métricas de execução", en="Execution metrics"),
            _localized_phrase(language, pt="Próximos passos", en="Next steps"),
        ]
    return [
        _localized_phrase(language, pt="Contexto da decisão", en="Decision context"),
        _localized_phrase(language, pt="Evidências principais", en="Core evidence"),
        _localized_phrase(language, pt="Estrutura de execução", en="Execution structure"),
        _localized_phrase(language, pt="Riscos e objeções", en="Risks and objections"),
        _localized_phrase(language, pt="Próximos passos", en="Next steps"),
        _localized_phrase(language, pt="Recomendação final", en="Final recommendation"),
    ]


def _derive_slide_copy(
    briefing: "BriefingInput",
    *,
    language: str,
    domain: str,
    candidate_story_mode: bool,
    narrative_archetype: str,
    option_titles: tuple[str, str] | None = None,
) -> dict[str, object]:
    if candidate_story_mode:
        return {
            "agenda_title": _localized_phrase(language, pt="Agenda da conversa", en="Interview agenda"),
            "agenda_subtitle": _localized_phrase(language, pt="História, profundidade técnica e valor para a empresa", en="Story, technical depth and company value"),
            "section_title": _localized_phrase(language, pt="Trajetória, impacto e execução", en="Story, impact and execution"),
            "section_label": _localized_phrase(language, pt="Narrativa", en="Narrative"),
            "context_title": _localized_phrase(language, pt="Minha trajetória e proposta de valor", en="My story and value proposition"),
            "context_subtitle": _localized_phrase(language, pt="O fio condutor que sustenta minha candidatura", en="The throughline behind my candidacy"),
            "cards_title": _localized_phrase(language, pt="Por que sou um candidato forte para AI Engineer", en="Why I am a strong AI Engineer candidate"),
            "cards_subtitle": _localized_phrase(language, pt="Os três pilares que me diferenciam para a vaga", en="Three reasons I stand out for the role"),
            "image_text_title": _localized_phrase(language, pt="Projetos de IA mais relevantes", en="Most relevant AI projects"),
            "image_text_subtitle": _localized_phrase(language, pt="Casos que mostram profundidade, execução e resultado", en="Cases that show depth, execution and outcomes"),
            "metrics_title": _localized_phrase(language, pt="Resultados mensuráveis", en="Measured outcomes"),
            "metrics_subtitle": _localized_phrase(language, pt="Indicadores que reforçam impacto e senioridade", en="Signals that reinforce impact and seniority"),
            "chart_title": _localized_phrase(language, pt="Comparativo dos principais sinais", en="Comparison of the main signals"),
            "chart_subtitle": _localized_phrase(language, pt="Leitura quantitativa da minha trajetória", en="Quantitative readout of my track record"),
            "timeline_title": _localized_phrase(language, pt="Sequência de execução", en="Execution sequence"),
            "timeline_subtitle": _localized_phrase(language, pt="Como estruturo problema, solução e entrega", en="How I structure problem, solution and delivery"),
            "comparison_title": _localized_phrase(language, pt="Alternativas e trade-offs", en="Alternatives and trade-offs"),
            "comparison_subtitle": _localized_phrase(language, pt="Como penso escolhas técnicas e de produto", en="How I think through technical and product choices"),
            "two_column_title": _localized_phrase(language, pt="Stack técnica + visão de negócio", en="Technical depth + business view"),
            "two_column_subtitle": _localized_phrase(language, pt="Como conecto arquitetura, produção e valor", en="How I connect architecture, production and value"),
            "two_column_left_title": _localized_phrase(language, pt="Profundidade técnica", en="Technical depth"),
            "two_column_right_title": _localized_phrase(language, pt="Produto e negócio", en="Product and business"),
            "faq_title": _localized_phrase(language, pt="Perguntas críticas da entrevista", en="Critical interview questions"),
            "table_title": _localized_phrase(language, pt="O que cada capítulo prova", en="What each chapter proves"),
            "table_subtitle": _localized_phrase(language, pt="O deck como tese explícita de contratação", en="Turn the deck into an explicit hiring thesis"),
            "table_columns": [
                _localized_phrase(language, pt="Capítulo", en="Chapter"),
                _localized_phrase(language, pt="O que prova", en="What it proves"),
                _localized_phrase(language, pt="Por que importa", en="Why it matters"),
            ],
            "summary_title": _localized_phrase(language, pt="Por que sou um forte fit para a vaga", en="Why I am a strong fit for the role"),
            "summary_subtitle": _localized_phrase(language, pt="A síntese do valor que entrego", en="The condensed value I bring"),
            "closing_title": _localized_phrase(language, pt="O valor que posso gerar", en="The value I can generate"),
            "closing_quote": _localized_phrase(language, pt="Eu combino profundidade em IA, disciplina de produção e visão de negócio para gerar resultados concretos em ambientes exigentes.", en="I combine AI depth, production discipline and business judgment to create concrete outcomes in demanding environments."),
            "recommended_move_footer": _localized_phrase(language, pt="Execução com senioridade", en="Execution with seniority"),
        }

    generic_copy = {
        "agenda_title": _localized_phrase(language, pt="Agenda da decisão", en="Decision agenda"),
        "agenda_subtitle": _localized_phrase(language, pt="Sequência executiva construída a partir do briefing", en="Executive sequence built from the briefing"),
        "section_title": _localized_phrase(language, pt="A decisão em jogo", en="The decision at stake"),
        "section_label": _localized_phrase(language, pt="Contexto", en="Context"),
        "context_title": _localized_phrase(language, pt="O contexto que exige decisão", en="The context that requires a decision"),
        "context_subtitle": _localized_phrase(language, pt="Diagnóstico e tese central do deck", en="Diagnosis and core thesis of the deck"),
        "cards_title": _localized_phrase(language, pt="Três mensagens que sustentam a recomendação", en="Three messages behind the recommendation"),
        "cards_subtitle": _localized_phrase(language, pt="O que a liderança deve reter", en="What leadership should retain"),
        "image_text_title": _localized_phrase(language, pt="Como a narrativa vira alavanca de execução", en="How the narrative becomes execution leverage"),
        "image_text_subtitle": _localized_phrase(language, pt="Do diagnóstico à ação com clareza executiva", en="From diagnosis to action with executive clarity"),
        "metrics_title": _localized_phrase(language, pt="Métricas que importam", en="Metrics that matter"),
        "metrics_subtitle": _localized_phrase(language, pt="Os sinais que mais pesam na decisão", en="Signals that matter most for the decision"),
        "chart_title": _localized_phrase(language, pt="Como os sinais se comparam", en="How the signals compare"),
        "chart_subtitle": _localized_phrase(language, pt="Leitura rápida dos indicadores críticos", en="Quick read on the critical indicators"),
        "timeline_title": _localized_phrase(language, pt="Sequência recomendada", en="Recommended sequence"),
        "timeline_subtitle": _localized_phrase(language, pt="O ritmo de execução mais seguro para avançar", en="The safest execution sequence to move forward"),
        "comparison_title": _localized_phrase(language, pt="Opções em jogo", en="Options in play"),
        "comparison_subtitle": _localized_phrase(language, pt="Comparação direta das alternativas", en="Direct comparison of the alternatives"),
        "two_column_title": _localized_phrase(language, pt="Diagnóstico atual vs movimento recomendado", en="Current diagnosis vs recommended move"),
        "two_column_subtitle": _localized_phrase(language, pt="O contraste que sustenta a decisão", en="The contrast behind the decision"),
        "two_column_left_title": _localized_phrase(language, pt="Diagnóstico atual", en="Current diagnosis"),
        "two_column_right_title": _localized_phrase(language, pt="Movimento recomendado", en="Recommended move"),
        "faq_title": _localized_phrase(language, pt="Perguntas críticas da liderança", en="Critical leadership questions"),
        "table_title": _localized_phrase(language, pt="Plano de execução", en="Execution plan"),
        "table_subtitle": _localized_phrase(language, pt="Como transformar a recomendação em sequência prática", en="How to turn the recommendation into a practical sequence"),
        "table_columns": [
            _localized_phrase(language, pt="Fase", en="Phase"),
            _localized_phrase(language, pt="Foco", en="Focus"),
            _localized_phrase(language, pt="Por que importa", en="Why it matters"),
        ],
        "summary_title": _localized_phrase(language, pt="Síntese executiva da recomendação", en="Executive synthesis of the recommendation"),
        "summary_subtitle": _localized_phrase(language, pt="A leitura final para decisão", en="The final read for decision-making"),
        "closing_title": _localized_phrase(language, pt="Mensagem final", en="Closing message"),
        "closing_quote": _localized_phrase(language, pt="Um briefing forte só vira decisão forte quando a narrativa, a sequência e a execução ficam claras para a liderança.", en="A strong briefing becomes a strong decision only when the narrative, sequence and execution are clear to leadership."),
        "recommended_move_footer": _localized_phrase(language, pt="Mover com clareza", en="Move with clarity"),
    }

    if narrative_archetype == "review":
        generic_copy.update(
            {
                "agenda_title": _localized_phrase(language, pt="Agenda do review", en="Review agenda"),
                "section_title": _localized_phrase(language, pt="Leitura atual do cenário", en="Current readout"),
                "context_title": _localized_phrase(language, pt="O que o review mostra com clareza", en="What the review shows clearly"),
                "cards_title": _localized_phrase(language, pt="Três sinais que merecem atenção", en="Three signals that deserve attention"),
                "timeline_title": _localized_phrase(language, pt="Sequência de correção", en="Correction sequence"),
                "summary_title": _localized_phrase(language, pt="Síntese do review", en="Review synthesis"),
            }
        )
    elif narrative_archetype == "proposal":
        generic_copy.update(
            {
                "section_title": _localized_phrase(language, pt="Por que esta proposta", en="Why this proposal"),
                "context_title": _localized_phrase(language, pt="O problema que a proposta resolve", en="The problem the proposal solves"),
                "cards_title": _localized_phrase(language, pt="Três diferenciais da proposta", en="Three differentiators of the proposal"),
                "comparison_title": _localized_phrase(language, pt="Alternativas consideradas", en="Alternatives considered"),
                "summary_title": _localized_phrase(language, pt="Síntese da proposta", en="Proposal synthesis"),
                "closing_title": _localized_phrase(language, pt="Movimento recomendado", en="Recommended move"),
            }
        )
    elif narrative_archetype == "strategy":
        generic_copy.update(
            {
                "section_title": _localized_phrase(language, pt="A escolha estratégica em jogo", en="The strategic choice in play"),
                "context_title": _localized_phrase(language, pt="O contexto que pede reposicionamento", en="The context that requires repositioning"),
                "cards_title": _localized_phrase(language, pt="Três razões para esta tese", en="Three reasons behind this thesis"),
                "summary_title": _localized_phrase(language, pt="Síntese estratégica", en="Strategic synthesis"),
            }
        )
    elif narrative_archetype == "operating":
        generic_copy.update(
            {
                "section_title": _localized_phrase(language, pt="Como a operação deve mudar", en="How the operating model should change"),
                "context_title": _localized_phrase(language, pt="O gargalo operacional central", en="The core operating bottleneck"),
                "timeline_title": _localized_phrase(language, pt="Sequência operacional recomendada", en="Recommended operating sequence"),
                "table_title": _localized_phrase(language, pt="Plano operacional", en="Operating plan"),
                "summary_title": _localized_phrase(language, pt="Síntese operacional", en="Operating synthesis"),
            }
        )

    if option_titles:
        generic_copy["comparison_title"] = _shorten_words(f"{option_titles[0]} vs {option_titles[1]}", max_words=8) or generic_copy["comparison_title"]

    if domain == "sales":
        generic_copy.update(
            {
                "section_title": _localized_phrase(language, pt="Por que este movimento agora", en="Why this move now"),
                "context_title": _localized_phrase(language, pt="O problema comercial que o copiloto resolve", en="The sales problem the copilot solves"),
                "cards_title": _localized_phrase(language, pt="Três alavancas para liderança comercial", en="Three levers for sales leadership"),
                "image_text_title": _localized_phrase(language, pt="Como o copiloto entra no fluxo comercial", en="How the copilot fits the commercial workflow"),
                "metrics_title": _localized_phrase(language, pt="Impacto esperado no funil", en="Expected pipeline impact"),
                "chart_title": _localized_phrase(language, pt="Onde o impacto aparece primeiro", en="Where impact appears first"),
                "timeline_title": _localized_phrase(language, pt="Roteiro de rollout", en="Rollout roadmap"),
                "two_column_title": _localized_phrase(language, pt="Diagnóstico comercial vs movimento recomendado", en="Commercial diagnosis vs recommended move"),
                "faq_title": _localized_phrase(language, pt="Riscos e objeções do board", en="Board risks and objections"),
                "table_title": _localized_phrase(language, pt="Plano de decisão em 90 dias", en="90-day decision plan"),
                "summary_title": _localized_phrase(language, pt="Recomendação final ao board", en="Final recommendation to the board"),
                "closing_title": _localized_phrase(language, pt="Decisão recomendada", en="Recommended decision"),
                "closing_quote": _localized_phrase(language, pt="Começar com um workflow de alta tração reduz risco, acelera aprendizado e mostra valor cedo para a liderança.", en="Starting with a high-traction workflow reduces risk, accelerates learning and proves value early to leadership."),
            }
        )
    elif domain == "product":
        generic_copy.update(
            {
                "section_title": _localized_phrase(language, pt="Onde o roadmap perdeu foco", en="Where the roadmap lost focus"),
                "context_title": _localized_phrase(language, pt="O diagnóstico que pede decisão", en="The diagnosis that demands a decision"),
                "cards_title": _localized_phrase(language, pt="Três sinais de diluição do roadmap", en="Three signs of roadmap dilution"),
                "image_text_title": _localized_phrase(language, pt="Como transformar diagnóstico em foco", en="How to turn diagnosis into focus"),
                "metrics_title": _localized_phrase(language, pt="KPIs que pedem correção de rota", en="KPIs that require a course correction"),
                "chart_title": _localized_phrase(language, pt="Comparativo dos sinais críticos", en="Comparison of the critical signals"),
                "timeline_title": _localized_phrase(language, pt="Sequência recomendada para o trimestre", en="Recommended sequence for the quarter"),
                "two_column_title": _localized_phrase(language, pt="Situação atual vs foco recomendado", en="Current situation vs recommended focus"),
                "faq_title": _localized_phrase(language, pt="Riscos e trade-offs da mudança", en="Risks and trade-offs of the change"),
                "table_title": _localized_phrase(language, pt="Plano de foco para o trimestre", en="Quarter focus plan"),
                "summary_title": _localized_phrase(language, pt="Recomendação para o operating review", en="Recommendation for the operating review"),
                "closing_title": _localized_phrase(language, pt="A escolha que aumenta execução", en="The choice that improves execution"),
                "closing_quote": _localized_phrase(language, pt="Menos frentes, melhor sequência e decisões mais rápidas aumentam a qualidade de execução do roadmap.", en="Fewer fronts, clearer sequencing and faster decisions improve roadmap execution quality."),
            }
        )

    return generic_copy


def _normalize_outline_label(value: str) -> str:
    cleaned = value.strip(" -*•\t:;,.\n")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"^(?:e|and)\s+", "", cleaned, flags=re.IGNORECASE)
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    replacements = {
        "apresentação pessoal": "Apresentação pessoal",
        "stack técnica": "Stack técnica",
        "stack tecnico": "Stack técnica",
        "projetos mais relevantes": "Projetos mais relevantes",
        "arquiteturas/fluxos de ia": "Arquiteturas e fluxos de IA",
        "resultados mensuráveis": "Resultados mensuráveis",
        "resultados mensuraveis": "Resultados mensuráveis",
        "forma de pensar em produção e escalabilidade": "Produção e escalabilidade",
        "forma de pensar em producao e escalabilidade": "Produção e escalabilidade",
        "como trabalho com produto e negócio": "Produto e negócio",
        "como trabalho com produto e negocio": "Produto e negócio",
        "um fechamento forte mostrando o valor que posso gerar para a empresa": "Valor que posso gerar",
        "fechamento forte mostrando o valor que posso gerar para a empresa": "Valor que posso gerar",
    }
    if lowered in replacements:
        return replacements[lowered]
    return _sentence_case(cleaned) or cleaned


def _strip_intent_request_prefix(sentence: str) -> str:
    normalized = sentence.strip()
    prefixes = [
        r"^quero\s+(?:uma?|um)\s+(?:apresenta(?:ç|c)ão|deck|pitch)\s+(?:para|sobre|de)\s+",
        r"^preciso\s+de\s+(?:uma?|um)\s+(?:apresenta(?:ç|c)ão|deck|pitch)\s+(?:para|sobre|de)\s+",
        r"^crie\s+(?:uma?|um)\s+(?:apresenta(?:ç|c)ão|deck|pitch)\s+(?:para|sobre|de)\s+",
        r"^monte\s+(?:uma?|um)\s+(?:apresenta(?:ç|c)ão|deck|pitch)\s+(?:para|sobre|de)\s+",
    ]
    lowered = normalized.lower()
    for pattern in prefixes:
        updated = re.sub(pattern, "", lowered, count=1, flags=re.IGNORECASE)
        if updated != lowered:
            normalized = normalized[len(normalized) - len(updated) :]
            lowered = updated
            break
    return normalized.strip()


def _extract_include_items(intent_text: str) -> list[str]:
    include_items: list[str] = []
    for line in intent_text.splitlines():
        if ":" not in line:
            continue
        prefix, rest = line.split(":", 1)
        if prefix.strip().lower() not in {"inclua", "include", "incluir"}:
            continue
        normalized_rest = rest.replace("/", " e ")
        candidates = [segment.strip() for segment in re.split(r",|;", normalized_rest) if segment.strip()]
        for candidate in candidates:
            cleaned = _normalize_outline_label(candidate)
            if cleaned and cleaned not in include_items:
                include_items.append(cleaned)
    return include_items


def _extract_style_recommendations(intent_text: str) -> list[str]:
    recommendations: list[str] = []
    lowered = intent_text.lower()

    def add(message: str) -> None:
        if message not in recommendations:
            recommendations.append(message)

    if any(keyword in lowered for keyword in ["visual premium", "premium", "sofisticado", "moderno", "profissional"]):
        add("Use a premium, modern and highly professional visual language.")
    if any(keyword in lowered for keyword in ["storytelling claro", "storytelling", "narrativa clara"]):
        add("Build a clear narrative arc with sharp executive transitions between slides.")
    if any(keyword in lowered for keyword in ["pouca poluição visual", "pouca poluicao visual", "sem poluição visual", "sem poluicao visual"]):
        add("Keep slides visually clean, with low clutter and strong whitespace discipline.")
    if any(keyword in lowered for keyword in ["foco em impacto", "impacto", "mensurável", "mensuravel"]):
        add("Prioritize measurable impact and decision-relevant outcomes over generic claims.")
    if any(keyword in lowered for keyword in ["confiante", "sofisticado", "objetivo"]):
        add("Keep the tone confident, sophisticated and objective.")

    return recommendations


def _infer_audience_from_intent(intent_text: str) -> str | None:
    lowered = intent_text.lower()
    if any(keyword in lowered for keyword in ["entrevista", "vaga", "candidato", "recrutador", "hiring"]):
        return "Hiring panel"
    if any(keyword in lowered for keyword in ["board", "conselho", "steerco", "diretoria", "executivo"]):
        return "Executive leadership"
    if any(keyword in lowered for keyword in ["cliente", "sales", "produto", "product"]):
        return "Business stakeholders"
    return None


def _derive_title_from_intent(intent_text: str) -> str:
    first_sentence = _split_sentences(intent_text)[0] if _split_sentences(intent_text) else intent_text.strip()
    interview_match = re.search(r"entrevista\s+de\s+([^\n\.,:;]+)", first_sentence, flags=re.IGNORECASE)
    if interview_match:
        role = interview_match.group(1)
        role = re.split(r"\s+(?:que|mostrando|para|com)\s+", role, maxsplit=1, flags=re.IGNORECASE)[0].strip(" :-,;")
        if role:
            return _sentence_case(_shorten_words(f"Entrevista de {role}", max_words=4)) or "Entrevista"

    product_review_match = re.search(r"product operating review", first_sentence, flags=re.IGNORECASE)
    if product_review_match:
        return "Product operating review"

    candidate = _strip_intent_request_prefix(first_sentence)
    lowered_first_sentence = first_sentence.lower()
    subject_patterns = [
        r"\bexplicando\s+por\s+que\s+(?:devemos|deveria|vale\s+a\s+pena)\s+(.+)",
        r"\bpor\s+que\s+(?:devemos|deveria|vale\s+a\s+pena)\s+(.+)",
        r"\bsobre\s+(.+)",
    ]
    audience_placeholders = {
        "o board",
        "board",
        "o conselho",
        "conselho",
        "a diretoria",
        "diretoria",
        "o comitê",
        "comitê",
        "comite",
        "hiring panel",
    }
    normalized_candidate = candidate.strip().lower()
    if any(
        normalized_candidate == placeholder or normalized_candidate.startswith(f"{placeholder} ")
        for placeholder in audience_placeholders
    ):
        for pattern in subject_patterns:
            match = re.search(pattern, lowered_first_sentence, flags=re.IGNORECASE)
            if match:
                extracted = first_sentence[match.start(1) : match.end(1)].strip(" :-,;")
                if extracted:
                    candidate = extracted
                    break
    split_markers = [" mostrando ", " explicando ", " sobre ", " com ", " para mostrar ", " para explicar "]
    lowered_candidate = candidate.lower()
    for marker in split_markers:
        if marker in lowered_candidate:
            candidate = candidate[: lowered_candidate.index(marker)]
            break
    candidate = candidate.strip(" :-,;")
    candidate = re.sub(r"\s+", " ", candidate)
    if not candidate:
        candidate = "Intent-driven presentation"
    shortened = _shorten_words(candidate, max_words=8) or candidate
    return _sentence_case(shortened) or "Intent-driven presentation"


def _derive_objective_from_intent(intent_text: str) -> str | None:
    first_sentence = _split_sentences(intent_text)[0] if _split_sentences(intent_text) else intent_text.strip()
    lowered = first_sentence.lower()
    for marker in [" mostrando ", " explicando ", " para mostrar ", " para explicar "]:
        if marker in lowered:
            objective = first_sentence[lowered.index(marker) + len(marker) :].strip(" :-,;")
            return _sentence_case(objective)
    stripped = _strip_intent_request_prefix(first_sentence)
    return _sentence_case(stripped)


def _derive_context_from_intent(intent_text: str) -> str | None:
    lines = [line.strip() for line in intent_text.splitlines() if line.strip()]
    context_lines = [
        line
        for line in lines[1:]
        if any(
            keyword in line.lower()
            for keyword in ["visual", "storytelling", "poluição visual", "poluicao visual", "impacto", "tom", "confiante", "sofisticado", "objetivo"]
        )
    ]
    if not context_lines:
        sentences = _split_sentences(intent_text)
        if len(sentences) > 1:
            context_lines = sentences[1:3]
    return _shorten_words(" ".join(context_lines), max_words=40)


def _infer_intent_domain(intent_text: str) -> str:
    lowered = intent_text.lower()
    if any(keyword in lowered for keyword in ["entrevista", "interview", "candidate", "candidato", "hiring", "vaga", "ai engineer"]):
        return "interview"
    if any(keyword in lowered for keyword in ["sales", "revenue", "pipeline", "qbr", "forecast", "vendas"]):
        return "sales"
    if any(keyword in lowered for keyword in ["product", "roadmap", "quarter", "trimestre", "priorit", "produto"]):
        return "product"
    if any(keyword in lowered for keyword in ["board", "conselho", "diretoria", "steerco", "strategy", "estratég"]):
        return "board"
    return "generic"


def _derive_metrics_from_intent(intent_text: str) -> list[dict[str, object]]:
    lowered = intent_text.lower()
    if not any(
        keyword in lowered
        for keyword in ["metric", "metrics", "métrica", "métricas", "metricas", "kpi", "impact", "impacto", "performance", "resultado", "%"]
    ):
        return []

    domain = _infer_intent_domain(intent_text)
    if domain == "sales":
        return [
            {"label": "Rep hours saved", "value": "12h/mo", "detail": "prep + follow-up automation", "trend": "+32%"},
            {"label": "Forecast quality", "value": "+18%", "detail": "more consistent pipeline narrative", "trend": "improving"},
            {"label": "Conversion lift", "value": "+9%", "detail": "pilot upside target", "trend": "pilot"},
        ]
    if domain == "product":
        return [
            {"label": "Roadmap focus", "value": "+25%", "detail": "more effort on top priorities", "trend": "target"},
            {"label": "Decision speed", "value": "-30%", "detail": "fewer unresolved debates", "trend": "faster"},
            {"label": "Execution confidence", "value": "+20 pts", "detail": "clearer sequencing", "trend": "target"},
        ]
    if domain == "board":
        return [
            {"label": "Time saved", "value": "25%", "detail": "remove repetitive executive prep", "trend": "upside"},
            {"label": "Quality lift", "value": "+15%", "detail": "more consistent decision material", "trend": "upside"},
            {"label": "Adoption rate", "value": "60%", "detail": "narrow rollout target", "trend": "pilot"},
        ]
    return [
        {"label": "Efficiency", "value": "+20%", "detail": "operational improvement target", "trend": "upside"},
        {"label": "Quality", "value": "+15%", "detail": "better output consistency", "trend": "upside"},
        {"label": "Adoption", "value": "60%", "detail": "initial rollout target", "trend": "pilot"},
    ]


def _derive_milestones_from_intent(intent_text: str) -> list[dict[str, object]]:
    lowered = intent_text.lower()
    if not any(keyword in lowered for keyword in ["timeline", "rollout", "roadmap", "milestone", "quarter", "trimestre", "sequência", "sequencia", "phase", "next-quarter"]):
        return []

    domain = _infer_intent_domain(intent_text)
    if domain == "sales":
        return [
            {"title": "Scope the workflow", "detail": "Choose one leadership workflow with executive pull.", "phase": "Weeks 1-2"},
            {"title": "Pilot with sales leaders", "detail": "Launch a constrained rollout with instrumentation and feedback.", "phase": "Weeks 3-6"},
            {"title": "Scale what works", "detail": "Expand only after adoption and quality signals are clear.", "phase": "Weeks 7-12"},
        ]
    if domain == "product":
        return [
            {"title": "Refocus the roadmap", "detail": "Consolidate work into fewer priority bets.", "phase": "Month 1"},
            {"title": "Sequence execution", "detail": "Align teams on dependencies, trade-offs and decision cadence.", "phase": "Month 2"},
            {"title": "Deliver the new plan", "detail": "Execute the focused roadmap with visible milestones.", "phase": "Quarter"},
        ]
    return [
        {"title": "Diagnose", "detail": "Clarify the highest-value scope and the real decision to be made.", "phase": "Phase 1"},
        {"title": "Pilot", "detail": "Run a narrow implementation with clear success metrics.", "phase": "Phase 2"},
        {"title": "Scale", "detail": "Expand only once the pilot proves repeatable value.", "phase": "Phase 3"},
    ]


def _derive_options_from_intent(intent_text: str) -> list[dict[str, object]]:
    lowered = intent_text.lower()
    if not any(keyword in lowered for keyword in ["comparison", "comparação", "comparacao", "opções", "opcoes", "options", "trade-off", "tradeoff", "versus"]):
        return []

    domain = _infer_intent_domain(intent_text)
    if domain == "product":
        return [
            {
                "title": "Keep the current roadmap",
                "body": "Preserve existing commitments and absorb the coordination cost.",
                "bullets": ["Lower short-term disruption", "Keeps dilution in place", "Slower strategic learning"],
                "footer": "Lower friction, weaker focus",
            },
            {
                "title": "Refocus now",
                "body": "Collapse the roadmap into fewer bets with clearer sequencing.",
                "bullets": ["Sharper prioritization", "Clearer trade-offs", "Higher execution confidence"],
                "footer": "Higher focus, stronger control",
            },
        ]
    return [
        {
            "title": "Launch now",
            "body": "Capture upside quickly with a focused initiative and visible executive sponsorship.",
            "bullets": ["Faster learning", "Earlier value capture", "Higher execution pressure"],
            "footer": "Speed-first",
        },
        {
            "title": "Pilot first",
            "body": "De-risk the rollout through a narrow pilot and explicit success gates.",
            "bullets": ["Cleaner instrumentation", "Lower adoption risk", "Slower upside realization"],
            "footer": "Risk-managed",
        },
    ]


def _derive_faqs_from_intent(intent_text: str) -> list[dict[str, object]]:
    lowered = intent_text.lower()
    if not any(keyword in lowered for keyword in ["risk", "risks", "riscos", "faq", "objeções", "objecoes", "trade-off", "tradeoff", "concerns"]):
        return []

    domain = _infer_intent_domain(intent_text)
    if domain == "sales":
        return [
            {"question": "What are the main rollout risks?", "answer": "Adoption drag, workflow sprawl and weak instrumentation if scope expands too early."},
            {"question": "What trade-off are we making?", "answer": "We choose a narrower launch in exchange for clearer learning and higher decision confidence."},
            {"question": "How will success be measured?", "answer": "Track time saved, quality lift and sustained usage in the chosen workflow."},
        ]
    if domain == "product":
        return [
            {"question": "What is the biggest risk of refocusing?", "answer": "Short-term disruption to stakeholders used to the current roadmap shape."},
            {"question": "What trade-off are we accepting?", "answer": "We trade breadth for stronger sequencing, clarity and execution confidence."},
            {"question": "How do we know the new plan is working?", "answer": "Look for faster decisions, better roadmap coherence and visible milestone progress."},
        ]
    return [
        {"question": "What is the main execution risk?", "answer": "Trying to scale the initiative before the narrow scope has proved repeatable value."},
        {"question": "What trade-off are we making?", "answer": "We reduce breadth to gain clarity, control and cleaner evidence."},
        {"question": "How will success be judged?", "answer": "By measurable impact, adoption quality and a cleaner decision narrative."},
    ]


def _is_candidate_story_briefing(briefing: BriefingInput) -> bool:
    text = " ".join(
        filter(
            None,
            [
                briefing.title,
                briefing.subtitle,
                briefing.audience,
                briefing.objective,
                briefing.briefing_text,
            ],
        )
    ).lower()
    return any(keyword in text for keyword in ["entrevista", "interview", "candidate", "candidato", "vaga", "hiring"])


def _has_any_keyword(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _derive_interview_key_messages(briefing: BriefingInput) -> list[str]:
    text = " ".join(filter(None, [briefing.objective, briefing.context, briefing.briefing_text]))
    messages: list[str] = []

    def add(message: str) -> None:
        if message not in messages:
            messages.append(message)

    if _has_any_keyword(text, ["trajetória", "trajetoria", "apresentação pessoal", "apresentacao pessoal"]):
        add("Trajetória em IA com foco em impacto real.")
    if _has_any_keyword(text, ["projeto", "projetos", "arquitetura", "fluxos de ia", "stack"]):
        add("Projetos relevantes mostram profundidade técnica e pragmatismo.")
    if _has_any_keyword(text, ["negócio", "negocio", "produto", "soluções técnicas", "solucoes tecnicas"]):
        add("Traduzo problemas de negócio em soluções técnicas claras.")
    if _has_any_keyword(text, ["produção", "producao", "escalabilidade", "mensurável", "mensuravel"]):
        add("Penso em produção, escala e resultado mensurável.")

    fallbacks = [
        "Conecto contexto estratégico, design técnico e execução.",
        "Tenho repertório para atuar em ambientes exigentes.",
    ]
    for item in fallbacks:
        add(item)
    return messages[:4]


def _derive_interview_project_bullets(briefing: BriefingInput) -> list[str]:
    text = " ".join(filter(None, [briefing.objective, briefing.briefing_text]))
    bullets: list[str] = []

    def add(message: str) -> None:
        if message not in bullets:
            bullets.append(message)

    if _has_any_keyword(text, ["projetos", "projeto"]):
        add("Projetos selecionados evidenciam profundidade técnica e priorização.")
    if _has_any_keyword(text, ["arquitetura", "fluxos de ia", "stack"]):
        add("Arquiteturas e fluxos mostram como estruturo sistemas robustos.")
    if _has_any_keyword(text, ["resultado", "mensurável", "mensuravel", "impacto"]):
        add("Cada caso reforça impacto, métrica e aprendizado de negócio.")
    if _has_any_keyword(text, ["produção", "producao", "escalabilidade"]):
        add("A narrativa inclui produção, confiabilidade e escalabilidade.")

    if not bullets:
        bullets = [
            "Projetos relevantes demonstram consistência entre profundidade técnica e resultado.",
            "Arquiteturas escolhidas mostram clareza de decisão e senso de trade-off.",
            "Os casos reforçam minha capacidade de executar em contexto real de negócio.",
        ]
    return bullets[:4]


def _derive_interview_execution_columns(briefing: BriefingInput) -> list[dict[str, object]]:
    return [
        {
            "title": "Profundidade técnica",
            "body": "Estruturo soluções de IA com foco em arquitetura, qualidade e confiabilidade.",
            "bullets": [
                "Escolha de stack aderente ao problema",
                "Observabilidade, fallback e evolução contínua",
            ],
            "footer": "Execução técnica com maturidade",
        },
        {
            "title": "Produto e negócio",
            "body": "Conecto a solução ao fluxo do usuário, à decisão de negócio e ao valor em produção.",
            "bullets": [
                "Traduzo ambiguidade em recortes executáveis",
                "Priorizo adoção, impacto e mensuração",
            ],
            "footer": "IA aplicada com foco em valor",
        },
    ]


def _derive_interview_capability_cards(briefing: BriefingInput) -> list[dict[str, object]]:
    text = " ".join(filter(None, [briefing.objective, briefing.context, briefing.briefing_text])).lower()
    cards: list[dict[str, object]] = []

    def add(title: str, body: str, footer: str) -> None:
        if len(cards) >= 3:
            return
        if any(existing["title"] == title for existing in cards):
            return
        cards.append({"title": title, "body": body, "footer": footer})

    if any(keyword in text for keyword in ["trajetória", "trajetoria", "apresentação pessoal", "apresentacao pessoal"]):
        add(
            "Trajetória com substância",
            "Apresento evolução consistente em IA aplicada, unindo repertório técnico, clareza narrativa e senso de prioridade.",
            "História com senioridade",
        )
    if any(keyword in text for keyword in ["stack", "arquitetura", "fluxos de ia", "arquiteturas e fluxos"]):
        add(
            "Stack e arquitetura de IA",
            "Desenho pipelines, integrações e fluxos de IA com atenção a qualidade técnica, observabilidade e robustez operacional.",
            "Profundidade técnica",
        )
    if any(keyword in text for keyword in ["projeto", "impacto", "resultado", "mensurável", "mensuravel"]):
        add(
            "Projetos com impacto real",
            "Conecto execução técnica a resultados tangíveis, mostrando como IA resolve problemas relevantes de produto e negócio.",
            "Impacto comprovável",
        )
    if any(keyword in text for keyword in ["produção", "producao", "escalabilidade", "produção e escalabilidade", "producao e escalabilidade"]):
        add(
            "Produção e escala",
            "Penso em deployment, custo, confiabilidade, fallback, monitoramento e evolução contínua desde o desenho da solução.",
            "Pensamento de produção",
        )
    if any(keyword in text for keyword in ["produto", "negócio", "negocio"]):
        add(
            "Produto + negócio",
            "Traduzo ambiguidade de negócio em recortes técnicos viáveis, priorizando adoção, valor e velocidade de aprendizado.",
            "Parceria com negócio",
        )

    fallbacks = [
        (
            "Clareza estratégica",
            "Organizo a narrativa para mostrar por que minhas decisões técnicas importam para a empresa e para o produto.",
            "Visão executiva",
        ),
        (
            "Execução end-to-end",
            "Consigo ir do problema ao desenho da solução, implementação, operacionalização e melhoria contínua.",
            "Entrega completa",
        ),
        (
            "Maturidade para ambiente exigente",
            "Atuo com autonomia, rigor e senso de impacto em contextos com alta barra técnica e de negócio.",
            "Fit para high standards",
        ),
    ]
    for title, body, footer in fallbacks:
        add(title, body, footer)
    return cards[:3]


def _derive_interview_story_rows(briefing: BriefingInput) -> list[list[str]]:
    rows: list[list[str]] = []

    def proof_for_outline_item(item: str) -> str:
        lowered = item.lower()
        if any(keyword in lowered for keyword in ["trajetória", "trajetoria", "apresentação pessoal", "apresentacao pessoal"]):
            return "Senioridade, ownership e narrativa pessoal"
        if any(keyword in lowered for keyword in ["stack", "arquitetura", "fluxos de ia", "arquiteturas"]):
            return "Profundidade técnica e design de sistemas"
        if any(keyword in lowered for keyword in ["projeto", "resultado", "mensurável", "mensuravel"]):
            return "Impacto aplicado e capacidade de execução"
        if any(keyword in lowered for keyword in ["produção", "producao", "escalabilidade"]):
            return "Maturidade de produção e escala"
        if any(keyword in lowered for keyword in ["produto", "negócio", "negocio"]):
            return "Tradução entre negócio, produto e engenharia"
        if any(keyword in lowered for keyword in ["fechamento", "valor"]):
            return "Proposta de valor clara para a empresa"
        return "Relevância direta para a decisão de contratação"

    for item in briefing.outline[:5]:
        rows.append([item, proof_for_outline_item(item), "Evidência para a decisão de contratação"])
    if not rows:
        rows = [
            ["Trajetória e posicionamento", "Senioridade e clareza narrativa", "Mostra fit para uma função exigente"],
            ["Projetos e impacto", "Execução aplicada com resultado", "Prova capacidade de entregar valor"],
            ["Produção e negócio", "Visão de escala e produto", "Reduz risco de execução"],
        ]
    return rows[:5]


def _parse_numeric_signal(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.strip().replace(",", "")
    multiplier = 1.0
    lowered = cleaned.lower()
    if lowered.endswith("%"):
        cleaned = cleaned[:-1]
    elif lowered.endswith("x"):
        cleaned = cleaned[:-1]
    elif lowered.endswith("k"):
        cleaned = cleaned[:-1]
        multiplier = 1_000.0
    elif lowered.endswith("m"):
        cleaned = cleaned[:-1]
        multiplier = 1_000_000.0
    elif lowered.endswith("b"):
        cleaned = cleaned[:-1]
        multiplier = 1_000_000_000.0

    match = re.search(r"-?\d+(?:\.\d+)?", cleaned.replace("$", ""))
    if not match:
        return None
    return float(match.group()) * multiplier


def summarize_text_to_executive_bullets(
    text: str | None,
    *,
    max_bullets: int = 3,
    max_words: int = 14,
) -> list[str]:
    if not text:
        return []

    segments = [segment.strip() for segment in re.split(r"[\n\.\?!;]+", text) if segment.strip()]
    bullets: list[str] = []
    for segment in segments:
        words = segment.split()
        shortened = " ".join(words[:max_words]).strip()
        if len(words) > max_words:
            shortened += "..."
        if shortened and shortened not in bullets:
            bullets.append(shortened)
        if len(bullets) >= max_bullets:
            break
    return bullets


class BriefingMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    detail: str | None = None
    trend: str | None = None

    @field_validator("label", "value", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)

    @field_validator("detail", "trend", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class BriefingMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    detail: str | None = None
    phase: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("detail", "phase", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)


class BriefingOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str | None = None
    bullets: list[str] = Field(default_factory=list)
    footer: str | None = None

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator("body", "footer", mode="before")
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("bullets")
    @classmethod
    def clean_bullets(cls, bullets: list[str]) -> list[str]:
        return _clean_string_list(bullets, field_name="option bullet")

    @model_validator(mode="after")
    def validate_has_content(self) -> "BriefingOption":
        if not (self.body or self.bullets):
            raise ValueError("briefing option requires body or bullets")
        return self


class BriefingFAQ(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str

    @field_validator("question", "answer", mode="before")
    @classmethod
    def clean_required_fields(cls, value: object, info) -> str | object:
        return _clean_required_text(value, info.field_name)


class BriefingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    subtitle: str | None = None
    audience: str | None = None
    objective: str | None = None
    context: str | None = None
    briefing_text: str | None = None
    client_name: str | None = None
    author: str | None = None
    date: str | None = None
    theme: str = "executive_premium_minimal"
    outline: list[str] = Field(default_factory=list)
    key_messages: list[str] = Field(default_factory=list)
    metrics: list[BriefingMetric] = Field(default_factory=list)
    milestones: list[BriefingMilestone] = Field(default_factory=list)
    options: list[BriefingOption] = Field(default_factory=list)
    faqs: list[BriefingFAQ] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    closing_quote: str | None = None

    @field_validator(
        "title",
        mode="before",
    )
    @classmethod
    def clean_title(cls, value: object) -> str | object:
        return _clean_required_text(value, "title")

    @field_validator(
        "subtitle",
        "audience",
        "objective",
        "context",
        "briefing_text",
        "client_name",
        "author",
        "date",
        "closing_quote",
        mode="before",
    )
    @classmethod
    def clean_optional_fields(cls, value: object) -> str | None | object:
        return _clean_optional_text(value)

    @field_validator("outline", "key_messages", "recommendations")
    @classmethod
    def clean_string_lists(cls, values: list[str], info) -> list[str]:
        return _clean_string_list(values, field_name=info.field_name)

    @field_validator("theme", mode="before")
    @classmethod
    def normalize_theme(cls, value: object) -> str | object:
        if value is None:
            return "executive_premium_minimal"
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
        return normalized or "executive_premium_minimal"

    @model_validator(mode="after")
    def validate_minimum_signal(self) -> "BriefingInput":
        if not any(
            [
                self.objective,
                self.context,
                self.briefing_text,
                self.key_messages,
                self.metrics,
                self.milestones,
                self.options,
                self.faqs,
                self.recommendations,
                self.outline,
            ]
        ):
            raise ValueError("briefing requires at least one content signal beyond the title")
        return self

    @classmethod
    def from_path(cls, path: str | Path) -> "BriefingInput":
        json_path = Path(path)
        if not json_path.exists():
            raise FileNotFoundError(f"Briefing JSON not found: {json_path}")
        return cls.model_validate(json.loads(json_path.read_text(encoding="utf-8")))


def build_briefing_from_intent_text(
    intent_text: str,
    *,
    title: str | None = None,
) -> BriefingInput:
    normalized_intent = str(intent_text or "").strip()
    if not normalized_intent:
        raise ValueError("intent_text cannot be empty")

    language = _infer_prompt_language(normalized_intent)
    domain = _infer_intent_domain(normalized_intent)
    narrative_archetype = _infer_narrative_archetype(normalized_intent)
    candidate_story_mode = _infer_audience_from_intent(normalized_intent) == "Hiring panel"
    resolved_title = (title or "").strip() or _derive_title_from_intent(normalized_intent)
    include_items = _extract_include_items(normalized_intent) or _default_outline_for_prompt(
        language=language,
        domain=domain,
        candidate_story_mode=candidate_story_mode,
        narrative_archetype=narrative_archetype,
    )
    recommendations = _extract_style_recommendations(normalized_intent)
    objective = _derive_objective_from_intent(normalized_intent)
    context = _derive_context_from_intent(normalized_intent)
    subtitle = None
    if include_items:
        subtitle = " · ".join(include_items[:3])
    raw_key_messages = (
        _derive_interview_key_messages(
            BriefingInput.model_validate(
                {
                    "title": resolved_title,
                    "briefing_text": normalized_intent,
                    "objective": objective,
                    "context": context,
                    "outline": include_items,
                    "recommendations": recommendations,
                }
            )
        )
        if candidate_story_mode
        else summarize_text_to_executive_bullets(normalized_intent, max_bullets=4)
    )
    key_messages = (
        raw_key_messages
        if candidate_story_mode
        else _condense_messages(raw_key_messages, max_items=4, max_words=10)
    )
    metrics = _derive_metrics_from_intent(normalized_intent)
    milestones = _derive_milestones_from_intent(normalized_intent)
    options = _derive_options_from_intent(normalized_intent)
    faqs = _derive_faqs_from_intent(normalized_intent)

    return BriefingInput.model_validate(
        {
            "title": resolved_title,
            "subtitle": subtitle,
            "audience": _infer_audience_from_intent(normalized_intent),
            "objective": objective,
            "context": context,
            "briefing_text": normalized_intent,
            "outline": include_items,
            "key_messages": key_messages,
            "recommendations": recommendations,
            "metrics": metrics,
            "milestones": milestones,
            "options": options,
            "faqs": faqs,
        }
    )


def build_minimal_briefing_from_intent_text(
    intent_text: str,
    *,
    title: str | None = None,
) -> BriefingInput:
    normalized_intent = str(intent_text or "").strip()
    if not normalized_intent:
        raise ValueError("intent_text cannot be empty")

    resolved_title = (title or "").strip() or _derive_title_from_intent(normalized_intent)
    include_items = _extract_include_items(normalized_intent)
    subtitle = " · ".join(include_items[:3]) if include_items else None
    return BriefingInput.model_validate(
        {
            "title": resolved_title,
            "subtitle": subtitle,
            "audience": _infer_audience_from_intent(normalized_intent),
            "objective": _derive_objective_from_intent(normalized_intent),
            "context": _derive_context_from_intent(normalized_intent),
            "briefing_text": normalized_intent,
        }
    )


def suggest_image_queries_from_briefing(
    briefing: BriefingInput,
    *,
    max_suggestions: int = 4,
) -> list[str]:
    suggestions: list[str] = []

    def add_suggestion(value: str | None) -> None:
        if not value:
            return
        cleaned = value.strip()
        if cleaned and cleaned not in suggestions:
            suggestions.append(cleaned)

    add_suggestion(f"{briefing.title} executive presentation background")

    title_lower = briefing.title.lower()
    if "sales" in title_lower or "revenue" in title_lower:
        add_suggestion("sales leadership dashboard and pipeline review")
    if "product" in title_lower:
        add_suggestion("product strategy roadmap workshop")
    if "strategy" in title_lower:
        add_suggestion("executive strategy offsite discussion")

    if briefing.metrics:
        add_suggestion("executive KPI dashboard with growth trend lines")
    if briefing.milestones:
        add_suggestion("program roadmap timeline and milestone workshop")
    if len(briefing.options) == 2:
        add_suggestion("decision workshop with comparison whiteboard")
    if briefing.audience:
        add_suggestion(f"{briefing.audience} leadership meeting")

    return suggestions[:max_suggestions]


def derive_briefing_freeform_signals(briefing: BriefingInput) -> dict[str, object]:
    freeform_text = briefing.briefing_text
    if not freeform_text:
        return {
            "objective": briefing.objective,
            "context": briefing.context,
            "outline": briefing.outline,
            "key_messages": briefing.key_messages,
            "recommendations": briefing.recommendations,
        }

    sentences = _split_sentences(freeform_text)
    paragraphs = [segment.strip() for segment in freeform_text.splitlines() if segment.strip()]
    summary_bullets = summarize_text_to_executive_bullets(freeform_text, max_bullets=6, max_words=14)

    def _contains_any(value: str, keywords: tuple[str, ...]) -> bool:
        normalized = value.lower()
        return any(keyword in normalized for keyword in keywords)

    recommendation_sentences = [
        sentence
        for sentence in sentences
        if _contains_any(sentence, ("should", "recommend", "need to", "must", "focus", "prioritize", "start with"))
    ]

    derived_outline: list[str] = list(briefing.outline)
    if not derived_outline:
        derived_outline.append("Situation overview")
        if _contains_any(freeform_text, ("metric", "kpi", "growth", "revenue", "%", "pipeline", "performance")):
            derived_outline.append("Performance signals")
        if _contains_any(freeform_text, ("roadmap", "timeline", "milestone", "phase", "rollout", "month")):
            derived_outline.append("Execution timeline")
        if _contains_any(freeform_text, ("option", "alternative", "choice", "compare", "versus")):
            derived_outline.append("Option framing")
        if _contains_any(freeform_text, ("question", "risk", "concern", "objection", "faq")):
            derived_outline.append("Executive FAQ")
        derived_outline.append("Recommendation")

    return {
        "objective": briefing.objective or (sentences[0] if sentences else None),
        "context": briefing.context or _shorten_words(paragraphs[0] if paragraphs else freeform_text, max_words=45),
        "outline": derived_outline,
        "key_messages": briefing.key_messages or summary_bullets[:4],
        "recommendations": briefing.recommendations or recommendation_sentences[:3] or summary_bullets[-2:],
    }


def _slide_image_context_hints(*, slide_type: str, title_context: str) -> dict[str, object]:
    hints: dict[str, dict[str, object]] = {
        "title": {
            "asset_style": "editorial executive hero background",
            "composition_notes": "Use a premium landscape image with strong negative space for cover typography.",
            "focal_point": {"x": 0.52, "y": 0.34},
        },
        "bullets": {
            "asset_style": "leadership workshop documentary photo",
            "composition_notes": "Prefer a contextual business scene with one cleaner side for narrative overlay.",
            "focal_point": {"x": 0.56, "y": 0.42},
        },
        "metrics": {
            "asset_style": "clean analytics dashboard or control-room visual",
            "composition_notes": "Prefer structured analytical imagery with the core signal cluster near the center.",
            "focal_point": {"x": 0.5, "y": 0.44},
        },
        "timeline": {
            "asset_style": "roadmap planning wall or milestone workshop",
            "composition_notes": "Prefer a wide planning visual with the main roadmap artifact centered slightly above mid-frame.",
            "focal_point": {"x": 0.5, "y": 0.4},
        },
        "comparison": {
            "asset_style": "decision workshop whiteboard with side-by-side framing",
            "composition_notes": "Prefer imagery that implies contrast and keeps both sides visually balanced.",
            "focal_point": {"x": 0.5, "y": 0.42},
        },
        "faq": {
            "asset_style": "boardroom Q&A discussion scene",
            "composition_notes": "Prefer a calm meeting image with evenly distributed visual weight and limited clutter.",
            "focal_point": {"x": 0.5, "y": 0.38},
        },
        "summary": {
            "asset_style": "executive alignment or final decision moment",
            "composition_notes": "Prefer a premium closing visual with centered subject matter and preserved whitespace.",
            "focal_point": {"x": 0.52, "y": 0.36},
        },
    }

    resolved = dict(
        hints.get(
            slide_type,
            {
                "asset_style": "clean executive contextual photo",
                "composition_notes": "Prefer premium, uncluttered imagery with enough negative space for slide text.",
                "focal_point": {"x": 0.5, "y": 0.4},
            },
        )
    )

    if "sales" in title_context or "revenue" in title_context:
        if slide_type == "metrics":
            resolved["asset_style"] = "sales dashboard or pipeline forecast visual"
        elif slide_type in {"bullets", "summary"}:
            resolved["asset_style"] = "sales leadership meeting or forecast review"
    elif "product" in title_context:
        if slide_type == "timeline":
            resolved["asset_style"] = "product roadmap workshop visual"
        elif slide_type in {"bullets", "summary"}:
            resolved["asset_style"] = "product strategy offsite or prioritization workshop"
    elif "strategy" in title_context:
        if slide_type in {"title", "summary"}:
            resolved["asset_style"] = "executive strategy offsite hero visual"

    return resolved


def suggest_slide_image_queries_from_briefing(
    briefing: BriefingInput,
    *,
    max_queries_per_slide: int = 3,
) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []

    def _queries(*values: str | None) -> list[str]:
        deduped: list[str] = []
        for value in values:
            if not value:
                continue
            cleaned = value.strip()
            if cleaned and cleaned not in deduped:
                deduped.append(cleaned)
        return deduped[:max_queries_per_slide]

    title_context = briefing.title.lower()
    audience_context = briefing.audience or "executive leadership team"

    def _suggestion(
        *,
        slide_key: str,
        slide_type: str,
        title: str,
        queries: list[str],
    ) -> dict[str, object]:
        hints = _slide_image_context_hints(slide_type=slide_type, title_context=title_context)
        return {
            "slide_key": slide_key,
            "slide_type": slide_type,
            "title": title,
            "queries": queries,
            "asset_style": hints["asset_style"],
            "composition_notes": hints["composition_notes"],
            "focal_point": hints["focal_point"],
        }

    suggestions.append(
        _suggestion(
            slide_key="title",
            slide_type="title",
            title=briefing.title,
            queries=_queries(
                f"{briefing.title} executive presentation cover image",
                f"{audience_context} strategy meeting hero background",
            ),
        )
    )

    if briefing.objective or briefing.context or briefing.key_messages:
        suggestions.append(
            _suggestion(
                slide_key="situation_overview",
                slide_type="bullets",
                title="Situation overview",
                queries=_queries(
                    f"{briefing.title} business context workshop",
                    f"{audience_context} planning session",
                    "executive team discussion around business priorities",
                ),
            )
        )

    if briefing.metrics:
        metric_labels = ", ".join(metric.label for metric in briefing.metrics[:2])
        suggestions.append(
            _suggestion(
                slide_key="headline_metrics",
                slide_type="metrics",
                title="Headline metrics",
                queries=_queries(
                    f"executive KPI dashboard for {briefing.title}",
                    f"business performance dashboard showing {metric_labels}" if metric_labels else None,
                    "leadership dashboard with clean charts and metric cards",
                ),
            )
        )

    if briefing.milestones:
        milestone_titles = ", ".join(item.title for item in briefing.milestones[:3])
        suggestions.append(
            _suggestion(
                slide_key="execution_timeline",
                slide_type="timeline",
                title="Execution timeline",
                queries=_queries(
                    f"program roadmap timeline for {briefing.title}",
                    f"milestone planning workshop covering {milestone_titles}" if milestone_titles else None,
                    "strategy roadmap with milestone planning board",
                ),
            )
        )

    if len(briefing.options) == 2:
        left, right = briefing.options
        suggestions.append(
            _suggestion(
                slide_key="option_framing",
                slide_type="comparison",
                title="Option framing",
                queries=_queries(
                    f"executive decision workshop comparing {left.title} and {right.title}",
                    "comparison whiteboard for strategic options",
                    f"leadership team evaluating {briefing.title} scenarios",
                ),
            )
        )

    if len(briefing.faqs) >= 2:
        first_question = briefing.faqs[0].question
        suggestions.append(
            _suggestion(
                slide_key="executive_faq",
                slide_type="faq",
                title="Executive FAQ",
                queries=_queries(
                    f"executive Q&A session about {briefing.title}",
                    f"leadership meeting addressing question: {first_question}",
                    "boardroom discussion handling objections and decisions",
                ),
            )
        )

    if briefing.recommendations or briefing.key_messages:
        suggestions.append(
            _suggestion(
                slide_key="executive_summary",
                slide_type="summary",
                title="Executive summary",
                queries=_queries(
                    f"executive summary visual for {briefing.title}",
                    "leadership alignment and decision summary",
                    "final recommendation slide background for executive meeting",
                ),
            )
        )

    if "sales" in title_context or "revenue" in title_context:
        for suggestion in suggestions:
            if suggestion["slide_key"] == "headline_metrics":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "sales pipeline dashboard and revenue forecast review",
                )
            if suggestion["slide_key"] == "situation_overview":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "sales leadership meeting discussing pipeline and enablement",
                )
    elif "product" in title_context:
        for suggestion in suggestions:
            if suggestion["slide_key"] == "execution_timeline":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "product roadmap planning session with milestones",
                )
            if suggestion["slide_key"] == "situation_overview":
                suggestion["queries"] = _queries(
                    *suggestion["queries"],
                    "product strategy workshop with leadership team",
                )

    return suggestions


def _infer_agenda(briefing: BriefingInput) -> list[str]:
    derived = derive_briefing_freeform_signals(briefing)
    if derived["outline"]:
        return list(derived["outline"])[:6]

    agenda: list[str] = []
    if briefing.objective or briefing.context or briefing.key_messages:
        agenda.append("Situation overview")
    if briefing.metrics:
        agenda.append("Performance signals")
    if briefing.milestones:
        agenda.append("Execution timeline")
    if len(briefing.options) == 2:
        agenda.append("Option framing")
    if len(briefing.faqs) >= 2:
        agenda.append("Executive FAQ")
    agenda.append("Recommendation")
    return agenda[:6]


def review_presentation_density(spec: PresentationInput) -> dict[str, object]:
    warnings: list[str] = []
    slide_reviews: list[dict[str, object]] = []

    for index, slide in enumerate(spec.slides, start=1):
        issues: list[str] = []
        body_len = len(slide.body or "")

        if slide.type.value in {"agenda", "bullets", "summary", "image_text"}:
            if len(slide.bullets) > 5:
                issues.append("too many bullets for an executive slide")
            if body_len > 260:
                issues.append("body text is likely too dense")

        if slide.type.value == "timeline" and len(slide.timeline_items) > 4:
            issues.append("timeline may be visually dense")

        if slide.type.value in {"comparison", "two_column"}:
            columns = slide.comparison_columns or slide.two_column_columns
            for column in columns:
                if len(column.bullets) > 3:
                    issues.append(f"column '{column.title}' has too many bullets")

        if slide.type.value == "table":
            if len(slide.table_rows) > 6:
                issues.append("table has many rows for a single slide")
            if len(slide.table_columns) > 4:
                issues.append("table has many columns for executive readability")

        if slide.type.value == "faq" and len(slide.faq_items) > 3:
            issues.append("faq may be too crowded")

        if slide.type.value == "chart" and len(slide.chart_categories) > 6:
            issues.append("chart has many categories for a clean executive view")

        slide_reviews.append(
            {
                "slide_number": index,
                "slide_type": slide.type.value,
                "title": slide.title or slide.type.value,
                "issues": issues,
            }
        )
        for issue in issues:
            warnings.append(f"slide {index:02d} ({slide.title or slide.type.value}): {issue}")

    return {
        "status": "review" if warnings else "ok",
        "warning_count": len(warnings),
        "warnings": warnings,
        "slides": slide_reviews,
    }


def build_generation_feedback_from_review(
    review: dict[str, object],
    *,
    max_messages: int = 8,
) -> list[str]:
    messages: list[str] = []

    def add(message: str) -> None:
        normalized = message.strip()
        if normalized and normalized not in messages and len(messages) < max_messages:
            messages.append(normalized)

    if int(review.get("overflow_risk_count") or 0) > 0:
        add("Reduce slide density overall; prefer fewer bullets, shorter bodies, and more whitespace.")
    if int(review.get("clipping_risk_count") or 0) > 0:
        add("Keep content farther from slide edges and avoid long lines that may clip in the final layout.")
    if int(review.get("balance_warning_count") or 0) > 0:
        add("Balance content more evenly across panels and columns so no region looks overloaded.")

    for slide_review in review.get("top_risk_slides", []) or []:
        if not isinstance(slide_review, dict):
            continue
        slide_number = slide_review.get("slide_number")
        slide_type = str(slide_review.get("slide_type") or "slide")
        title = str(slide_review.get("title") or slide_type)
        if slide_type in {"agenda", "bullets", "summary", "image_text"}:
            add(f"Slide {slide_number} '{title}' should use at most 4 concise bullets and a shorter narrative body.")
        elif slide_type in {"comparison", "two_column"}:
            add(f"Slide {slide_number} '{title}' should distribute content more evenly across both columns and reduce per-column bullets.")
        elif slide_type == "timeline":
            add(f"Slide {slide_number} '{title}' should use fewer timeline items or shorter milestone text.")
        elif slide_type == "table":
            add(f"Slide {slide_number} '{title}' should reduce table rows/columns and simplify cell text.")
        elif slide_type == "faq":
            add(f"Slide {slide_number} '{title}' should keep fewer FAQ items with shorter answers.")
        else:
            add(f"Slide {slide_number} '{title}' should be rewritten with a tighter executive narrative and less dense content.")

        if len(messages) >= max_messages:
            break

    for slide_review in review.get("slides", []) or []:
        if len(messages) >= max_messages:
            break
        if not isinstance(slide_review, dict):
            continue
        issues = slide_review.get("issues") or []
        if not issues:
            continue
        title = str(slide_review.get("title") or slide_review.get("slide_type") or "slide")
        add(f"Address QA issues on '{title}': {'; '.join(str(issue) for issue in issues[:2])}.")

    return messages


def build_generation_feedback_from_preview(
    preview_result: dict[str, object],
    *,
    max_messages: int = 6,
) -> list[str]:
    messages: list[str] = []

    def add(message: str) -> None:
        normalized = message.strip()
        if normalized and normalized not in messages and len(messages) < max_messages:
            messages.append(normalized)

    artifact_review = preview_result.get("preview_artifact_review") or {}
    if artifact_review.get("status") not in {None, "ok"}:
        if int(artifact_review.get("safe_area_intrusion_count") or 0) > 0:
            add("Keep main content within safer margins and avoid intruding into edge-adjacent regions.")
        if int(artifact_review.get("body_edge_contact_count") or 0) > 0:
            add("Pull body content farther from slide boundaries before the footer region.")
        if int(artifact_review.get("footer_intrusion_count") or 0) > 0:
            add("Reduce lower-slide crowding so content stays farther from the footer line.")
        if int(artifact_review.get("corner_density_warning_count") or 0) > 0:
            add("Avoid packing important content into slide corners; preserve more whitespace there.")
        if int(artifact_review.get("edge_density_warning_count") or 0) > 0:
            add("Reduce aggressive edge packing and simplify composition near the slide perimeter.")

    visual_regression = preview_result.get("visual_regression") or {}
    if int(visual_regression.get("diff_count") or 0) > 0:
        add("Stabilize the visual composition so regenerated slides drift less from baseline previews.")

    return messages


def build_slide_critiques_from_review(
    spec: PresentationInput,
    review: dict[str, object],
    *,
    max_critiques: int = 8,
) -> list[dict[str, object]]:
    critiques: list[dict[str, object]] = []
    slide_lookup = {index: slide for index, slide in enumerate(spec.slides, start=1)}

    def _guidance_for_slide(slide_type: str, slide_title: str, issues: list[str]) -> list[str]:
        guidance: list[str] = []
        if slide_type in {"agenda", "bullets", "summary", "image_text"}:
            guidance.append("Keep at most 4 bullets and shorten each line to an executive takeaway.")
            guidance.append("Reduce narrative text so the core message is readable in a few seconds.")
        elif slide_type in {"comparison", "two_column"}:
            guidance.append("Balance both columns and reduce text asymmetry between left and right panels.")
            guidance.append("Prefer fewer bullets per column with sharper contrast between options.")
        elif slide_type == "timeline":
            guidance.append("Use fewer milestones or shorter milestone descriptions.")
        elif slide_type == "table":
            guidance.append("Reduce rows/columns and simplify cell text to key facts only.")
        elif slide_type == "faq":
            guidance.append("Keep fewer FAQ entries and shorten each answer to the essential decision point.")
        elif slide_type == "metrics":
            guidance.append("Trim supporting detail so each KPI remains visually dominant.")
        else:
            guidance.append("Tighten the narrative so the slide reads as an executive summary, not a draft note page.")

        for issue in issues[:2]:
            guidance.append(f"Address this review issue explicitly: {issue}.")
        return guidance[:4]

    for slide_review in review.get("slides", []) or []:
        if len(critiques) >= max_critiques:
            break
        if not isinstance(slide_review, dict):
            continue
        issues = [str(issue) for issue in (slide_review.get("issues") or [])]
        if not issues:
            continue
        slide_number = int(slide_review.get("slide_number") or 0)
        slide = slide_lookup.get(slide_number)
        slide_type = str(slide_review.get("slide_type") or (slide.type.value if slide else "slide"))
        title = str(slide_review.get("title") or (slide.title if slide else slide_type) or slide_type)
        likely_regions = [str(region) for region in (slide_review.get("likely_overflow_regions") or [])]
        critiques.append(
            {
                "slide_number": slide_number,
                "slide_type": slide_type,
                "title": title,
                "risk_level": slide_review.get("risk_level") or "low",
                "issues": issues,
                "likely_overflow_regions": likely_regions,
                "rewrite_guidance": _guidance_for_slide(slide_type, title, issues),
            }
        )

    return critiques


def build_llm_generation_contract() -> dict[str, object]:
    return {
        "schema_version": "ppt_creator.presentation_input.v1",
        "response_rules": {
            "return_json_only": True,
            "single_top_level_object": True,
            "presentation_required_fields": ["title", "theme"],
            "each_slide_requires_type": True,
            "use_only_supported_slide_types": True,
        },
        "generation_preferences": {
            "prefer_rich_layout_mix_when_helpful": True,
            "prefer_visual_storytelling_over_repeated_bullets": True,
            "use_cards_sections_metrics_and_comparisons_when_supported_by_content": True,
        },
        "quality_guardrails": {
            "prefer_prompt_specific_slide_titles": True,
            "avoid_generic_placeholder_titles": [
                "Situation overview",
                "Narrative frame",
                "Current context vs next move",
                "Action plan",
                "Executive summary",
                "Closing thought",
            ],
            "reuse_user_vocabulary_in_titles_and_bullets": True,
            "keep_output_language_consistent_with_briefing": True,
            "avoid_renderer_scaffolding_or_placeholder_copy": True,
            "prefer_narrative_archetype_consistency": True,
            "prefer_evidence_bearing_slides_for_strong_claims": True,
            "avoid_weak_qualitative_pseudo_metrics_without_evidence": True,
            "when_prompt_mentions_metrics_timeline_comparison_or_faq_use_matching_slide_types": True,
            "interview_or_candidate_decks_should_cover_story_projects_technical_depth_production_and_value": True,
        },
        "recommended_narrative_archetypes": [
            "decision",
            "review",
            "strategy",
            "profile",
            "proposal",
            "operating",
        ],
        "supported_themes": [
            "executive_premium_minimal",
            "consulting_clean",
            "dark_boardroom",
            "startup_minimal",
        ],
        "global_density_guidance": {
            "max_recommended_bullets_per_slide": 4,
            "max_recommended_timeline_items": 4,
            "max_recommended_faq_items": 3,
            "max_recommended_table_rows": 6,
            "max_recommended_table_columns": 4,
            "prefer_short_executive_sentences": True,
        },
        "supported_slide_types": {
            "title": {
                "required_fields": ["type", "title"],
                "optional_fields": ["subtitle", "eyebrow", "body", "layout_variant"],
                "layout_variants": ["split_panel", "hero_cover"],
            },
            "section": {
                "required_fields": ["type", "title"],
                "optional_fields": ["subtitle", "section_label", "eyebrow"],
            },
            "agenda": {
                "required_fields": ["type", "title", "bullets"],
                "optional_fields": ["subtitle", "body"],
            },
            "bullets": {
                "required_fields": ["type", "title", "bullets"],
                "optional_fields": ["subtitle", "body", "eyebrow", "layout_variant"],
                "layout_variants": ["insight_panel", "full_width"],
            },
            "cards": {
                "required_fields": ["type", "title", "cards"],
                "optional_fields": ["subtitle", "eyebrow"],
                "cards_rules": {"exactly_three_cards": True},
            },
            "image_text": {
                "required_fields": ["type", "title"],
                "optional_fields": ["subtitle", "body", "bullets", "image_caption", "layout_variant"],
                "layout_variants": ["image_right", "image_left"],
            },
            "metrics": {
                "required_fields": ["type", "title", "metrics"],
                "optional_fields": ["subtitle", "layout_variant"],
                "layout_variants": ["standard", "compact"],
            },
            "chart": {
                "required_fields": ["type", "title", "chart_categories", "chart_series"],
                "optional_fields": ["subtitle", "body", "layout_variant"],
                "layout_variants": ["column", "bar", "line"],
            },
            "timeline": {
                "required_fields": ["type", "title", "timeline_items"],
                "optional_fields": ["subtitle"],
            },
            "comparison": {
                "required_fields": ["type", "title", "comparison_columns"],
                "optional_fields": ["subtitle"],
            },
            "two_column": {
                "required_fields": ["type", "title", "two_column_columns"],
                "optional_fields": ["subtitle"],
            },
            "table": {
                "required_fields": ["type", "title", "table_columns", "table_rows"],
                "optional_fields": ["subtitle"],
            },
            "faq": {
                "required_fields": ["type", "title", "faq_items"],
                "optional_fields": ["subtitle"],
            },
            "summary": {
                "required_fields": ["type", "title"],
                "optional_fields": ["subtitle", "body", "bullets", "eyebrow"],
            },
            "closing": {
                "required_fields": ["type", "title"],
                "optional_fields": ["quote", "attribution"],
            },
        },
        "recommended_deck_blueprint": [
            "title",
            "agenda",
            "context slide (bullets or image_text)",
            "evidence slide (metrics or chart)",
            "structure slide (timeline/comparison/two_column/table/faq)",
            "summary",
            "closing",
        ],
    }


def build_briefing_analysis(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
    feedback_messages: list[str] | None = None,
) -> dict[str, object]:
    spec = generate_presentation_input_from_briefing(
        briefing,
        theme_name=theme_name,
        feedback_messages=feedback_messages,
    )
    derived_signals = derive_briefing_freeform_signals(briefing)
    summary_source = " ".join(
        filter(
            None,
            [
                str(derived_signals.get("objective") or "") or None,
                str(derived_signals.get("context") or "") or None,
                *(derived_signals.get("key_messages") or [])[:3],
                *(derived_signals.get("recommendations") or [])[:3],
            ],
        )
    )
    narrative_archetype = _infer_narrative_archetype(
        " ".join(
            filter(
                None,
                [briefing.title, briefing.subtitle, briefing.objective, briefing.context, briefing.briefing_text],
            )
        )
    )

    return {
        "briefing_title": briefing.title,
        "narrative_archetype": narrative_archetype,
        "theme": spec.presentation.theme,
        "generated_slide_count": len(spec.slides),
        "feedback_messages": feedback_messages or [],
        "llm_generation_contract": build_llm_generation_contract(),
        "executive_summary_bullets": (derived_signals.get("recommendations") or [])[:3]
        or summarize_text_to_executive_bullets(summary_source, max_bullets=3),
        "image_suggestions": suggest_image_queries_from_briefing(briefing),
        "slide_image_suggestions": suggest_slide_image_queries_from_briefing(briefing),
        "density_review": review_presentation_density(spec),
    }


def _build_card_items_from_messages(messages: list[str]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, message in enumerate(messages, start=1):
        normalized = message.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        title = (_shorten_words(normalized, max_words=4) or f"Point {index}").rstrip(" .:;!?")
        items.append(
            {
                "title": title or f"Point {index}",
                "body": normalized,
                "footer": "Executive talking point",
            }
        )
        if len(items) == 3:
            break
    return items


def generate_presentation_payload_from_briefing(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
    feedback_messages: list[str] | None = None,
) -> dict[str, object]:
    effective_theme = theme_name or briefing.theme
    compact_mode = bool(feedback_messages)
    prompt_text = " ".join(
        filter(
            None,
            [briefing.title, briefing.subtitle, briefing.objective, briefing.context, briefing.briefing_text],
        )
    )
    language = _infer_prompt_language(prompt_text)
    domain = _infer_intent_domain(prompt_text)
    narrative_archetype = _infer_narrative_archetype(prompt_text)
    derived_signals = derive_briefing_freeform_signals(briefing)
    candidate_story_mode = _is_candidate_story_briefing(briefing)
    resolved_outline = list(briefing.outline) or _default_outline_for_prompt(
        language=language,
        domain=domain,
        candidate_story_mode=candidate_story_mode,
        narrative_archetype=narrative_archetype,
    )
    resolved_metrics = list(briefing.metrics) or [
        BriefingMetric.model_validate(item)
        for item in _derive_metrics_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_milestones = list(briefing.milestones) or [
        BriefingMilestone.model_validate(item)
        for item in _derive_milestones_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_options = list(briefing.options) or [
        BriefingOption.model_validate(item)
        for item in _derive_options_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_faqs = list(briefing.faqs) or [
        BriefingFAQ.model_validate(item)
        for item in _derive_faqs_from_intent(briefing.briefing_text or briefing.title)
    ]
    option_titles = (
        (resolved_options[0].title, resolved_options[1].title)
        if len(resolved_options) >= 2
        else None
    )
    slide_copy = _derive_slide_copy(
        briefing,
        language=language,
        domain=domain,
        candidate_story_mode=candidate_story_mode,
        narrative_archetype=narrative_archetype,
        option_titles=option_titles,
    )
    raw_context_bullets = summarize_text_to_executive_bullets(
        " ".join(
            filter(
                None,
                [
                    str(derived_signals.get("objective") or "") or None,
                    str(derived_signals.get("context") or "") or None,
                    briefing.briefing_text,
                ],
            )
        ),
        max_bullets=3 if compact_mode else 4,
    )
    derived_context_bullets = _condense_messages(
        raw_context_bullets,
        max_items=3 if compact_mode else 4,
        max_words=8 if compact_mode else 10,
    )
    context_body = _shorten_words(
        str(derived_signals.get("context") or derived_signals.get("objective") or "") or None,
        max_words=22 if compact_mode else 28,
    )
    objective_body = _shorten_words(
        str(derived_signals.get("objective") or briefing.objective or "") or None,
        max_words=18 if compact_mode else 24,
    )
    slides: list[dict[str, object]] = [
        {
            "type": "title",
            "title": briefing.title,
            "subtitle": briefing.subtitle,
            "eyebrow": briefing.audience or "Briefing-generated deck",
            "layout_variant": "hero_cover",
            "body": objective_body,
        }
    ]

    agenda = (resolved_outline or _infer_agenda(briefing))[: 4 if compact_mode else 5]
    if agenda:
        slides.append(
            {
                "type": "agenda",
                "title": str(slide_copy["agenda_title"]),
                "subtitle": str(slide_copy["agenda_subtitle"]),
                "bullets": agenda,
            }
        )

    section_subtitle = _shorten_words(
        context_body or objective_body,
        max_words=12 if compact_mode else 14,
    )
    if agenda or section_subtitle:
        slides.append(
            {
                "type": "section",
                "title": str(slide_copy["section_title"]),
                "subtitle": section_subtitle,
                "section_label": str(slide_copy["section_label"]),
            }
        )

    key_messages = list(derived_signals.get("key_messages") or [])
    recommendations = list(derived_signals.get("recommendations") or [])
    if candidate_story_mode:
        key_messages = _derive_interview_key_messages(briefing)
    else:
        key_messages = _condense_messages(key_messages, max_items=4, max_words=9 if compact_mode else 10)
    recommendations = _condense_messages(
        recommendations,
        max_items=4,
        max_words=8 if compact_mode else 10,
    )
    context_bullets = (key_messages[:4] or derived_context_bullets[:4])
    if objective_body or context_body or context_bullets:
        slides.append(
            {
                "type": "bullets",
                "title": str(slide_copy["context_title"]),
                "subtitle": str(slide_copy["context_subtitle"]),
                "eyebrow": "Candidato" if candidate_story_mode else "Context",
                "body": context_body or objective_body,
                "bullets": context_bullets,
            }
        )

    card_messages: list[str] = []
    for source in (recommendations, key_messages, derived_context_bullets):
        for item in source:
            if item not in card_messages:
                card_messages.append(item)
    card_items = _derive_interview_capability_cards(briefing) if candidate_story_mode else _build_card_items_from_messages(card_messages)
    if len(card_items) == 3:
        slides.append(
            {
                "type": "cards",
                "title": str(slide_copy["cards_title"]),
                "subtitle": str(slide_copy["cards_subtitle"]),
                "eyebrow": "Candidate fit" if candidate_story_mode else "Narrative distillation",
                "cards": card_items,
            }
        )

    image_suggestions = suggest_slide_image_queries_from_briefing(briefing)
    situation_visual_hint = next(
        (item for item in image_suggestions if item.get("slide_key") == "situation_overview"),
        image_suggestions[0] if image_suggestions else None,
    )
    image_text_bullets = (
        _derive_interview_project_bullets(briefing)
        if candidate_story_mode
        else _condense_messages(key_messages or recommendations, max_items=3, max_words=9)
    )
    if (objective_body or context_body) and image_text_bullets:
        slides.append(
            {
                "type": "image_text",
                "title": str(slide_copy["image_text_title"]),
                "subtitle": str(slide_copy["image_text_subtitle"]),
                "body": _shorten_words(context_body or objective_body, max_words=12 if compact_mode else 16),
                "bullets": image_text_bullets,
                "image_caption": (
                    situation_visual_hint["asset_style"]
                    if situation_visual_hint
                    else "Use a contextual executive visual with clean whitespace."
                ),
            }
        )

    if resolved_metrics:
        slides.append(
            {
                "type": "metrics",
                "title": str(slide_copy["metrics_title"]),
                "subtitle": str(slide_copy["metrics_subtitle"]),
                "metrics": [metric.model_dump(mode="json") for metric in resolved_metrics[: (3 if compact_mode else 4)]],
            }
        )
        numeric_metrics = [
            (metric.label, _parse_numeric_signal(metric.value))
            for metric in resolved_metrics[: (4 if compact_mode else 5)]
        ]
        numeric_metrics = [(label, value) for label, value in numeric_metrics if value is not None]
        if len(numeric_metrics) >= 3:
            slides.append(
                {
                    "type": "chart",
                    "title": str(slide_copy["chart_title"]),
                    "subtitle": str(slide_copy["chart_subtitle"]),
                    "layout_variant": "bar",
                    "chart_categories": [label for label, _ in numeric_metrics],
                    "chart_series": [
                        {
                            "name": "Signal",
                            "values": [value for _, value in numeric_metrics],
                        }
                    ],
                }
            )

    if len(resolved_milestones) >= 2:
        slides.append(
            {
                "type": "timeline",
                "title": str(slide_copy["timeline_title"]),
                "subtitle": str(slide_copy["timeline_subtitle"]),
                "timeline_items": [
                    {
                        "title": milestone.title,
                        "body": _shorten_words(milestone.detail, max_words=8 if compact_mode else 10),
                        "tag": milestone.phase,
                    }
                    for milestone in resolved_milestones[: (4 if compact_mode else 5)]
                ],
            }
        )

    if len(resolved_options) == 2:
        slides.append(
            {
                "type": "comparison",
                "title": str(slide_copy["comparison_title"]),
                "subtitle": str(slide_copy["comparison_subtitle"]),
                "comparison_columns": [option.model_dump(mode="json") for option in resolved_options],
            }
        )

    if (context_body or objective_body) and (recommendations or key_messages):
        slides.append(
            {
                "type": "two_column",
                "title": str(slide_copy["two_column_title"]),
                "subtitle": str(slide_copy["two_column_subtitle"]),
                "two_column_columns": (
                    _derive_interview_execution_columns(briefing)
                    if candidate_story_mode
                    else [
                        {
                            "title": str(slide_copy["two_column_left_title"]),
                            "body": _shorten_words(context_body or objective_body, max_words=12 if compact_mode else 14),
                            "bullets": _condense_messages(key_messages, max_items=1 if compact_mode else 2, max_words=7),
                        },
                        {
                            "title": str(slide_copy["two_column_right_title"]),
                            "bullets": _condense_messages(recommendations or key_messages, max_items=2 if compact_mode else 3, max_words=7),
                            "footer": str(slide_copy["recommended_move_footer"]),
                        },
                    ]
                ),
            }
        )

    if len(resolved_faqs) >= 2:
        slides.append(
            {
                "type": "faq",
                "title": str(slide_copy["faq_title"]),
                "faq_items": [
                    {
                        "title": _shorten_words(faq.question, max_words=8 if compact_mode else 10) or faq.question,
                        "body": _shorten_words(faq.answer, max_words=10 if compact_mode else 12) or faq.answer,
                    }
                    for faq in resolved_faqs[: (3 if compact_mode else 4)]
                ],
            }
        )

    action_rows: list[list[str]] = []
    for index, milestone in enumerate(resolved_milestones[: (3 if compact_mode else 4)], start=1):
        action_rows.append(
            [
                milestone.phase or f"Step {index}",
                _shorten_words(milestone.title, max_words=5) or milestone.title,
                _shorten_words(milestone.detail, max_words=5) or str(slide_copy["recommended_move_footer"]),
            ]
        )
    if not action_rows:
        for index, recommendation in enumerate((recommendations or key_messages)[:3], start=1):
            action_rows.append(
                [
                    f"Step {index}",
                    _shorten_words(recommendation, max_words=5) or recommendation,
                    str(slide_copy["recommended_move_footer"]),
                ]
            )
    if action_rows:
        candidate_table_rows = [
            [
                _shorten_words(row[0], max_words=4) or row[0],
                _shorten_words(row[1], max_words=6) or row[1],
                _shorten_words(row[2], max_words=5) or row[2],
            ]
            for row in _derive_interview_story_rows(briefing)
        ]
        slides.append(
            {
                "type": "table",
                "title": str(slide_copy["table_title"]),
                "subtitle": str(slide_copy["table_subtitle"]),
                "table_columns": list(slide_copy["table_columns"]),
                "table_rows": (candidate_table_rows if candidate_story_mode else action_rows[:4]),
            }
        )

    summary_bullets = (
        [card["title"] for card in card_items]
        if candidate_story_mode and card_items
        else _condense_messages(
            recommendations or key_messages or derived_context_bullets,
            max_items=4,
            max_words=7 if compact_mode else 9,
        )
    )
    if summary_bullets or context_body or objective_body:
        slides.append(
            {
                "type": "summary",
                "title": str(slide_copy["summary_title"]),
                "subtitle": str(slide_copy["summary_subtitle"]),
                "body": _shorten_words(objective_body or context_body, max_words=10 if compact_mode else 14),
                "bullets": summary_bullets,
            }
        )

    slides.append(
        {
            "type": "closing",
            "title": str(slide_copy["closing_title"]),
            "quote": briefing.closing_quote or str(slide_copy["closing_quote"]),
        }
    )

    return {
        "presentation": {
            "title": briefing.title,
            "subtitle": briefing.subtitle,
            "author": briefing.author,
            "date": briefing.date,
            "theme": effective_theme,
            "client_name": briefing.client_name,
            "footer_text": f"{briefing.client_name} • Briefing deck" if briefing.client_name else None,
        },
        "slides": slides,
    }


def generate_presentation_input_from_briefing(
    briefing: BriefingInput,
    *,
    theme_name: str | None = None,
    feedback_messages: list[str] | None = None,
) -> PresentationInput:
    payload = generate_presentation_payload_from_briefing(
        briefing,
        theme_name=theme_name,
        feedback_messages=feedback_messages,
    )
    return PresentationInput.model_validate(payload)


def assess_generated_payload_quality(
    payload: dict[str, object],
    briefing: BriefingInput,
) -> dict[str, object]:
    spec = PresentationInput.model_validate(payload)
    prompt_text = " ".join(
        filter(
            None,
            [briefing.title, briefing.subtitle, briefing.objective, briefing.context, briefing.briefing_text],
        )
    )
    language = _infer_prompt_language(prompt_text)
    candidate_story_mode = _is_candidate_story_briefing(briefing)
    resolved_metrics = list(briefing.metrics) or [
        BriefingMetric.model_validate(item)
        for item in _derive_metrics_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_milestones = list(briefing.milestones) or [
        BriefingMilestone.model_validate(item)
        for item in _derive_milestones_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_options = list(briefing.options) or [
        BriefingOption.model_validate(item)
        for item in _derive_options_from_intent(briefing.briefing_text or briefing.title)
    ]
    resolved_faqs = list(briefing.faqs) or [
        BriefingFAQ.model_validate(item)
        for item in _derive_faqs_from_intent(briefing.briefing_text or briefing.title)
    ]

    required_slide_types = {"title", "summary", "closing"}
    if resolved_metrics:
        required_slide_types.add("metrics")
    if len(resolved_milestones) >= 2:
        required_slide_types.add("timeline")
    if len(resolved_options) >= 2:
        required_slide_types.add("comparison")
    if len(resolved_faqs) >= 2:
        required_slide_types.add("faq")
    if candidate_story_mode:
        required_slide_types.update({"image_text", "two_column"})

    slide_types = {slide.type.value for slide in spec.slides}
    missing_required_types = sorted(required_slide_types - slide_types)
    narrative_archetype = _infer_narrative_archetype(prompt_text)

    def _title_token(value: str | None) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    placeholder_tokens = {
        "situation overview",
        "narrative frame",
        "current context vs next move",
        "action plan",
        "executive summary",
        "closing thought",
        "three executive takeaways",
        "core narrative",
    }
    placeholder_titles = [
        slide.title
        for slide in spec.slides
        if _title_token(slide.title) in placeholder_tokens
    ]
    duplicate_titles = sorted(
        {
            token
            for token in [_title_token(slide.title) for slide in spec.slides]
            if token and token != "agenda" and sum(1 for slide in spec.slides if _title_token(slide.title) == token) > 1
        }
    )

    def _iter_payload_strings(value: object) -> list[str]:
        strings: list[str] = []
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                strings.append(cleaned)
            return strings
        if isinstance(value, list):
            for item in value:
                strings.extend(_iter_payload_strings(item))
            return strings
        if isinstance(value, dict):
            for item in value.values():
                strings.extend(_iter_payload_strings(item))
        return strings

    payload_strings = _iter_payload_strings(payload)
    payload_token_set = set(_extract_keyword_tokens(" ".join(payload_strings), min_length=4))

    weighted_keywords: list[tuple[str, float]] = []
    seen_weighted_keywords: set[str] = set()

    def _add_weighted_keywords(text: str | None, *, weight: float) -> None:
        for token in _extract_keyword_tokens(text, min_length=4):
            if token in seen_weighted_keywords:
                continue
            seen_weighted_keywords.add(token)
            weighted_keywords.append((token, weight))

    _add_weighted_keywords(briefing.title, weight=3.0)
    _add_weighted_keywords(briefing.objective, weight=2.5)
    _add_weighted_keywords(briefing.subtitle, weight=2.0)
    for item in briefing.outline[:6]:
        _add_weighted_keywords(item, weight=2.0)
    for item in briefing.key_messages[:4]:
        _add_weighted_keywords(item, weight=1.5)
    _add_weighted_keywords(briefing.context, weight=1.5)
    _add_weighted_keywords(briefing.briefing_text, weight=1.0)
    weighted_keywords = weighted_keywords[:18]
    weighted_total = sum(weight for _, weight in weighted_keywords) or 1.0
    matched_keywords = [token for token, weight in weighted_keywords if token in payload_token_set]
    matched_weight = sum(weight for token, weight in weighted_keywords if token in payload_token_set)
    specificity_score = round((matched_weight / weighted_total) * 100, 1)
    specificity_threshold = 35.0 if len(weighted_keywords) >= 6 else 25.0

    suspicious_default_tokens = {
        "executive lens",
        "what matters",
        "candidate name",
        "photo placeholder",
        "screenshot placeholder",
        "diagram placeholder",
        "editorial image placeholder",
        "editorial image unavailable",
        "analytical visual placeholder",
        "analytical visual unavailable",
        "approve the narrative, connect your content pipeline, and reuse the same renderer across future decks.",
        "keep decision-making crisp, reduce operational drag, and let human sellers spend more time in high-value conversations.",
        "executive lens: keep the message sparse, directional, and decision-friendly.",
    }
    default_copy_leaks = [
        text
        for text in payload_strings
        if _title_token(text) in suspicious_default_tokens
    ]

    weak_metric_tokens = {
        "high",
        "strong",
        "optimized",
        "optimised",
        "accelerated",
        "continuous",
        "ongoing",
        "alta",
        "alto",
        "forte",
        "otimizada",
        "otimizado",
        "acelerada",
        "acelerado",
        "contínua",
        "contínuo",
        "continua",
        "continuo",
    }
    weak_metric_values: list[str] = []
    for slide in spec.slides:
        if slide.type.value != "metrics":
            continue
        for metric in slide.metrics:
            normalized_value = _title_token(metric.value)
            if _parse_numeric_signal(metric.value) is None and normalized_value in weak_metric_tokens:
                weak_metric_values.append(f"{metric.label}: {metric.value}")

    evidence_slide_types = {"metrics", "chart", "table", "comparison", "timeline", "faq"}
    claim_markers = {
        "impacto",
        "valor",
        "diferencial",
        "diferenciais",
        "forte fit",
        "strong fit",
        "end_to_end",
        "end-to-end",
        "escalabilidade",
        "escalavel",
        "escalável",
        "produção",
        "producao",
        "resultado",
        "resultados",
        "melhor escolha",
        "best choice",
        "high impact",
        "alto impacto",
        "hired",
        "contratado",
    }
    proof_markers = {
        "kpi",
        "metric",
        "metrics",
        "métrica",
        "métricas",
        "metricas",
        "evidence",
        "proof",
        "case",
        "caso",
        "project",
        "projects",
        "projeto",
        "projetos",
        "stack",
        "deploy",
        "pipeline",
        "timeline",
        "comparison",
        "benchmark",
        "arquitetura",
        "dados",
        "modelos",
        "rollout",
    }

    def _contains_marker(text: str, markers: set[str]) -> bool:
        normalized = _title_token(text).replace(" ", "_")
        original = _title_token(text)
        return any(marker in normalized or marker in original for marker in markers)

    deck_level_claim_pressure = sum(1 for text in payload_strings if _contains_marker(text, claim_markers))
    deck_level_proof_pressure = sum(1 for text in payload_strings if _contains_marker(text, proof_markers) or _parse_numeric_signal(text) is not None)
    deck_has_structural_proof = any(slide.type.value in evidence_slide_types for slide in spec.slides)
    deck_has_textual_proof = deck_level_proof_pressure > 0
    claim_without_proof_slides: list[str] = []
    for slide in spec.slides:
        slide_payload = slide.model_dump(mode="json")
        slide_strings = _iter_payload_strings(slide_payload)
        if not slide_strings:
            continue
        has_claim = any(_contains_marker(text, claim_markers) for text in slide_strings)
        has_proof = slide.type.value in evidence_slide_types or any(
            _contains_marker(text, proof_markers) or _parse_numeric_signal(text) is not None
            for text in slide_strings
        )
        if has_claim and not has_proof and not deck_has_structural_proof and not deck_has_textual_proof:
            claim_without_proof_slides.append(slide.title or slide.type.value)

    problems: list[str] = []
    if missing_required_types:
        problems.append(f"missing requested slide types: {', '.join(missing_required_types)}")
    if len(placeholder_titles) >= 2:
        problems.append(f"too many generic placeholder titles: {', '.join(str(title) for title in placeholder_titles[:4])}")
    if duplicate_titles:
        problems.append(f"repeated slide titles: {', '.join(duplicate_titles[:3])}")
    if language == "pt" and placeholder_titles:
        problems.append("prompt is Portuguese but deck still contains generic English placeholder titles")
    if default_copy_leaks:
        problems.append(
            "deck still contains renderer/template scaffolding copy: "
            + ", ".join(default_copy_leaks[:4])
        )
    if weak_metric_values:
        problems.append(
            "metrics still use weak qualitative values instead of stronger evidence: "
            + ", ".join(weak_metric_values[:4])
        )
    if weighted_keywords and specificity_score < specificity_threshold:
        problems.append(
            f"specificity score too low ({specificity_score:.1f} < {specificity_threshold:.1f}); deck vocabulary does not reuse enough briefing-specific language"
        )
    if claim_without_proof_slides or (deck_level_claim_pressure >= 3 and not deck_has_structural_proof and deck_level_proof_pressure == 0):
        problems.append(
            "strong claims appear without enough proof-bearing structure: "
            + ", ".join(claim_without_proof_slides[:4] or ["deck-level claim pressure exceeds proof density"])
        )

    return {
        "should_fallback": bool(problems),
        "problems": problems,
        "missing_required_types": missing_required_types,
        "placeholder_titles": placeholder_titles,
        "duplicate_titles": duplicate_titles,
        "default_copy_leaks": default_copy_leaks,
        "weak_metric_values": weak_metric_values,
        "narrative_archetype": narrative_archetype,
        "specificity_score": specificity_score,
        "specificity_threshold": specificity_threshold,
        "matched_keywords": matched_keywords[:12],
        "missing_keywords": [token for token, _ in weighted_keywords if token not in payload_token_set][:12],
        "claim_without_proof_slides": claim_without_proof_slides,
        "slide_types": sorted(slide_types),
    }
