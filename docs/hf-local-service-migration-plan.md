# HF Local LLM Service → boundary de model server

Este arquivo existe como checklist operacional da migração para não misturar mais:

- **infra genérica de serving de modelo** (`hf_local_llm_service`)
- **lógica de domínio de decks** (`ppt_creator_ai` / `ppt_creator`)

## Boundary alvo

- `hf_local_llm_service` deve saber:
  - resolver provider/modelo
  - gerar texto genérico
  - operar chat persistido
  - gerar imagens
  - expor health, readiness, registry, jobs e uploads
- `hf_local_llm_service` não deve saber:
  - `BriefingInput`
  - `PresentationInput`
  - decks, slides, revise/critique de deck
- `ppt_creator_ai` deve saber:
  - construir prompts de deck
  - extrair JSON do output bruto
  - normalizar payload de slides
  - validar schema do deck
  - fazer revise/critique loops

## Checklist de implementação

- [x] Introduzir endpoint genérico de inferência (`/v1/generate`) no `hf_local_llm_service`
- [x] Migrar o fluxo principal do app para contrato genérico de text generation
- [x] Remover imports de `ppt_creator*` do core do serviço em health/API principal
- [x] Tirar `app_bridge` do path crítico de health/API/providers principais
- [x] Migrar `ppt_creator_ai.providers.local_service` para usar `/v1/generate`
- [x] Mover prompts / parsing / validação de deck para o `ppt_creator_ai`
- [x] Manter `/v1/presentation/*` apenas como compatibilidade temporária
- [x] Atualizar docs e testes do serviço para a identidade de model server
- [x] Atualizar docs e testes do app para o novo fluxo
- [x] Rodar testes dos dois lados e smoke tests HTTP

## Estado final desta etapa

- caminho **preferencial** do app: `ppt_creator_ai -> /v1/generate -> texto/JSON bruto -> parsing/validação no app`
- caminho **legado/compat**: `/v1/presentation/*`
- `app_bridge.py` ainda existe apenas para compatibilidade dos endpoints legados de deck, mas saiu do caminho crítico do servidor genérico

## Regra-guia

> O servidor sabe servir modelos. O app sabe fabricar decks.