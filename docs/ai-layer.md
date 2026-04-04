# AI layer

The app keeps the rendering engine and the LLM runtime independent on purpose.

Current boundary:

- `ppt_creator` / `ppt_creator_ai` stay inside the app
- real model execution stays outside the app, behind `local_service`
- Ollama remains an external dependency, not something bundled into the app container

## Recommended Ollama setup

Use the external service bridge with the local model:

```bash
export PPT_CREATOR_AI_SERVICE_URL=http://127.0.0.1:8788
export PPT_CREATOR_AI_SERVICE_PROVIDER=ollama
export PPT_CREATOR_AI_SERVICE_MODEL=nemotron-3-nano:30b-cloud
export PPT_CREATOR_AI_SERVICE_TIMEOUT_SECONDS=180
```

## Why the app now sends a generation contract

Direct raw prompts to Ollama tend to miss required schema details like slide `type`.

The safer approach is:

1. keep Ollama behind `hf_local_llm_service`
2. call the service through the generic `/v1/generate` boundary
3. send the briefing plus the app's explicit generation contract inside the prompt/request
4. require JSON-only output when the use case is deck generation
5. validate the result with `PresentationInput` inside the app

In other words:

- the **service** serves models and returns raw text/JSON
- the **app** interprets that output as a deck and validates domain schema

## Automated benchmark

The optional AI CLI now includes a benchmark to stress the prompt-to-deck path across multiple scenarios:

```bash
python -m ppt_creator_ai.cli benchmark outputs/ai_benchmark \
  --provider local_service \
  --write-json-decks \
  --report-json outputs/ai_benchmark/report.json
```

This reports:

- valid vs failed generations
- slide-type coverage
- QA review status / issue counts per scenario
- optional persisted deck JSON outputs for inspection