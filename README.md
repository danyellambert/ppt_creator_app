# PPT Creator

Gerador reutilizável de apresentações `.pptx` a partir de JSON estruturado, com foco em um visual **Executive Premium Minimal**.

> O playground de LLM continua existindo normalmente neste repositório. A documentação original do sandbox está em `README_hf_llm_playground.md`. Este `README.md` documenta o novo componente desacoplado `ppt_creator/`.

---

## Objetivo

O componente `ppt_creator` foi criado para manter um pipeline simples e portátil:

1. JSON estruturado entra
2. um renderizador Python gera um `.pptx`
3. o layout segue um tema consistente e reutilizável

Sem depender de PowerPoint, LibreOffice, Ollama, MLX, llama.cpp ou Transformers.

---

## Arquitetura

```text
ppt_creator/
├── __init__.py
├── api.py
├── cli.py
├── renderer.py
├── schema.py
├── templates.py
├── theme.py
└── layouts/
    ├── __init__.py
    ├── bullets.py
    ├── chart.py
    ├── comparison.py
    ├── cards.py
    ├── closing.py
    ├── image_text.py
    ├── metrics.py
    ├── section.py
    ├── timeline.py
    └── title.py
```

Separação principal:

- `schema.py`: contratos do JSON de entrada com `pydantic`
- `theme.py`: style tokens e tema `Executive Premium Minimal`
- `renderer.py`: renderizador central e utilitários comuns
- `layouts/`: implementação isolada por tipo de slide
- `cli.py`: interface de linha de comando

### Escopo do subprojeto

O `ppt_creator` é um componente **independente** dentro deste repositório.

Isso significa que:

- ele não depende de `transformers`
- ele não depende de Ollama, MLX ou llama.cpp
- ele não depende de nenhum modelo específico, incluindo PPTAgent
- o coração dele continua sendo: **JSON estruturado -> `.pptx`**

O repositório ainda contém scripts legados do playground geral de modelos, como `scripts/run_transformers.py`, mas esses arquivos **não fazem parte do núcleo do `ppt_creator`**.
Por isso, os fluxos de qualidade da Fase 2 passaram a focar no escopo do subprojeto:

- `ppt_creator/`
- `tests/`

Existe agora também uma camada **opcional e separada** em `ppt_creator_ai/`, usada para transformar um briefing estruturado em JSON de apresentação. Ela não interfere no núcleo do renderizador.

Além do tema base, o projeto agora também expõe temas prontos adicionais:

- `executive_premium_minimal`
- `consulting_clean`
- `dark_boardroom`
- `startup_minimal`

---

## Tipos de slide suportados

- `title`
- `section`
- `agenda`
- `bullets`
- `cards`
- `metrics`
- `chart`
- `image_text`
- `timeline`
- `comparison`
- `two_column`
- `table`
- `faq`
- `summary`
- `closing`

Todos suportam `speaker_notes`.

### Variantes de layout já suportadas

- `bullets`
  - `insight_panel` (padrão)
  - `full_width`
- `metrics`
  - `standard` (padrão)
  - `compact`
- `image_text`
  - `image_right` (padrão)
  - `image_left`
- `title`
  - `split_panel` (padrão)
  - `hero_cover`

Novos tipos executivos adicionados:

- `timeline`
  - sequência visual de 2 a 5 etapas
- `chart`
  - gráfico simples gerado por dados estruturados
- `comparison`
  - comparação lado a lado entre dois estados, opções ou estratégias
- `two_column`
  - narrativa em duas colunas para expor duas frentes ou perspectivas
- `table`
  - tabela executiva com colunas e linhas estruturadas
- `faq`
  - perguntas frequentes / appendix leve para objeções comuns
- `agenda`
  - sequência de tópicos para orientar a discussão
- `summary`
  - síntese executiva com mensagem principal e key takeaways

---

## Tema visual: Executive Premium Minimal

Direção implementada:

- base clara / off-white
- azul-marinho profundo como cor principal
- cinzas suaves para suporte
- destaque discreto em bronze sóbrio
- muito espaço em branco
- alinhamento rígido
- cards limpos com bordas leves
- sem excesso de shapes ou cores

O tema foi estruturado com tokens para facilitar futuros temas adicionais.

Hoje o tema já separa tokens em grupos para:

- canvas
- typography
- spacing
- grid
- colors
- components

---

## Formato do JSON

Estrutura de alto nível:

```json
{
  "presentation": {
    "title": "AI copilots for sales teams",
    "subtitle": "Executive strategy deck",
    "client_name": "Acme Corp",
    "author": "Your Name",
    "date": "2026-03-22",
    "theme": "executive_premium_minimal",
    "footer_text": "Acme Corp • Executive Review",
    "primary_color": "14263F",
    "secondary_color": "B08B5B"
  },
  "slides": [
    {
      "type": "title",
      "title": "AI copilots for sales teams",
      "subtitle": "How revenue teams scale quality without scaling friction",
      "speaker_notes": "Opening framing"
    }
  ]
}
```

Exemplo completo: `examples/ai_sales.json`

Exemplo de variante:

```json
{
  "type": "image_text",
  "title": "Operating model",
  "body": "Structured deployment model.",
  "layout_variant": "image_left"
}
```

Exemplo de `timeline`:

```json
{
  "type": "timeline",
  "title": "90-day rollout",
  "timeline_items": [
    {"title": "Diagnose", "body": "Identify the highest-value workflow"},
    {"title": "Pilot", "body": "Launch a constrained rollout"},
    {"title": "Scale", "body": "Operationalize the successful pattern"}
  ]
}
```

Exemplo de `chart`:

```json
{
  "type": "chart",
  "title": "Revenue trend",
  "layout_variant": "column",
  "chart_categories": ["Q1", "Q2", "Q3", "Q4"],
  "chart_series": [
    {"name": "Revenue", "values": [10.8, 11.9, 13.1, 14.2]}
  ]
}
```

Exemplo de `comparison`:

```json
{
  "type": "comparison",
  "title": "Before vs after",
  "comparison_columns": [
    {"title": "Before", "bullets": ["Manual prep", "Uneven quality"]},
    {"title": "After", "bullets": ["Structured workflow", "Consistent quality"]}
  ]
}
```

Campos adicionais de branding disponíveis em `presentation`:

- `client_name`
- `footer_text`
- `logo_path`
- `primary_color`
- `secondary_color`

`primary_color` e `secondary_color` aceitam hex de 6 dígitos e permitem adaptar o tema sem criar um tema novo do zero.

---

## Instalação local

Se quiser usar o ambiente local do playground:

```bash
./.conda-env/bin/python -m pip install -e .
./.conda-env/bin/python -m pip install -e ".[dev]"
```

Ou com o Python ativo no seu shell:

```bash
python -m pip install -e .
python -m pip install -e ".[dev]"
```

### VS Code / Pylance

Se o VS Code mostrar avisos como `Import could not be resolved` para `pytest` ou `pptx`, normalmente o problema é o interpretador Python errado no workspace.

Este repositório agora inclui `.vscode/settings.json` apontando para o ambiente local do projeto:

```text
.conda-env/bin/python
```

Se os avisos continuarem:

1. abra o Command Palette
2. rode `Python: Select Interpreter`
3. escolha `${workspaceFolder}/.conda-env/bin/python`
4. rode `Developer: Reload Window`

Isso costuma resolver os warnings do Pylance sem mudar o código.

---

## Como rodar localmente

Renderizar um deck:

```bash
python -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales.pptx
```

Forçar outro tema pronto:

```bash
python -m ppt_creator.cli render examples/product_strategy.json outputs/product_strategy.pptx \
  --theme consulting_clean
```

Aplicar override de branding por cor:

```bash
python -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales_branded.pptx \
  --primary-color 112233 --secondary-color AABBCC
```

Ou usando o helper:

```bash
bash bin/render_ppt_creator.sh examples/ai_sales.json outputs/ai_sales.pptx
```

Dry run com relatório:

```bash
python -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales.pptx \
  --dry-run --report-json outputs/ai_sales_report.json --check-assets
```

Se quiser já embutir uma revisão heurística de qualidade no relatório do render:

```bash
python -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales.pptx \
  --dry-run --review --report-json outputs/ai_sales_report.json
```

Esse relatório agora pode incluir:

- `severity_counts`
- `overflow_risk_count`
- `balance_warning_count`
- análise por slide

Rodar uma revisão heurística de qualidade:

```bash
python -m ppt_creator.cli review examples/ai_sales.json --report-json outputs/ai_sales_review.json
```

Esse comando gera um relatório com:

- score médio do deck
- issues por slide
- alertas de densidade, bullet overload, tabelas carregadas e assets ausentes

Renderização em lote:

```bash
python -m ppt_creator.cli render-batch examples outputs/batch \
  --pattern "*.json" --report-json outputs/batch_report.json
```

Gerar um template inicial por domínio:

```bash
python -m ppt_creator.cli template sales outputs/sales_template.json
```

Domínios disponíveis:

- `sales`
- `consulting`
- `strategy`
- `product`

Gerar JSON inicial a partir de um briefing estruturado:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json
```

Esse fluxo pertence à camada opcional `ppt_creator_ai/` e foi mantido separado do renderizador principal.

Se você quiser também um relatório heurístico com:

- resumo executivo em bullets
- sugestões de imagens/placeholders
- revisão de densidade dos slides gerados

rode:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --analysis-json outputs/briefing_sales_analysis.json
```

E agora também já dá para fazer um primeiro loop mais integrado de **geração + review + render**:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --review-json outputs/briefing_sales_review.json \
  --render-pptx outputs/briefing_sales_deck.pptx
```

Isso ajuda a aproximar o fluxo de:

- briefing
- geração de deck estruturado
- QA heurístico do deck gerado
- renderização final em `.pptx`

Também já existe uma primeira camada de **refinamento automático heurístico**:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --auto-refine --refine-passes 2 --report-json outputs/briefing_sales_generation_report.json
```

Esse fluxo tenta:

- gerar o deck inicial
- rodar review heurístico
- aplicar um pass de refinamento em slides mais densos
- reavaliar o deck refinado

Também já existe uma primeira camada de **regeneração automática baseada em feedback do review**:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --auto-regenerate --regenerate-passes 2 --report-json outputs/briefing_sales_regeneration_report.json
```

Esse fluxo tenta:

- gerar um deck inicial com o provider escolhido
- rodar review heurístico no deck gerado
- transformar os principais riscos em mensagens de feedback
- pedir uma nova geração ao provider com esse feedback

E agora você também pode acoplar **preview visual** diretamente nesse pipeline opcional:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --preview-dir outputs/briefing_sales_previews \
  --preview-report-json outputs/briefing_sales_preview_report.json
```

Isso aproxima ainda mais o ciclo de:

- briefing
- deck estruturado
- review heurístico
- preview visual
- render final

Você também pode listar os providers disponíveis da camada opcional:

```bash
python -m ppt_creator_ai.cli providers
```

E escolher explicitamente o provider usado no pipeline:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --provider heuristic
```

Também existe agora um provider opcional para **Ollama local**:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --provider ollama
```

Variáveis úteis:

```bash
export PPT_CREATOR_AI_OLLAMA_BASE_URL=http://127.0.0.1:11434
export PPT_CREATOR_AI_OLLAMA_MODEL=llama3.1
export PPT_CREATOR_AI_OLLAMA_CTX_SIZE=8192
export PPT_CREATOR_AI_OLLAMA_TEMPERATURE=0.2
export PPT_CREATOR_AI_OLLAMA_TIMEOUT_SECONDS=180
export PPT_CREATOR_AI_OLLAMA_RAW_OUTPUT_PATH=outputs/ollama_raw_output.txt
```

Pré-requisito típico:

```bash
ollama serve
ollama pull llama3.1
```

Também já existem providers remotos opcionais para **OpenAI** e **Anthropic**:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --provider openai

python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --provider anthropic
```

Variáveis úteis do OpenAI:

```bash
export OPENAI_API_KEY=...
export PPT_CREATOR_AI_OPENAI_MODEL=gpt-4o-mini
export PPT_CREATOR_AI_OPENAI_TIMEOUT_SECONDS=180
export PPT_CREATOR_AI_OPENAI_RAW_OUTPUT_PATH=outputs/openai_raw_output.txt
```

Variáveis úteis do Anthropic:

```bash
export ANTHROPIC_API_KEY=...
export PPT_CREATOR_AI_ANTHROPIC_MODEL=claude-3-5-haiku-latest
export PPT_CREATOR_AI_ANTHROPIC_TIMEOUT_SECONDS=180
export PPT_CREATOR_AI_ANTHROPIC_RAW_OUTPUT_PATH=outputs/anthropic_raw_output.txt
```

Se você quiser usar o seu GGUF local com `llama.cpp`/`llama-cli`, já existe um provider preparado para isso:

```bash
python -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_deck.json \
  --provider pptagent_local
```

Por padrão ele tenta resolver um modelo contendo `PPTAgent` dentro de `models/`. Você pode controlar isso com variáveis de ambiente:

```bash
export PPT_CREATOR_AI_GGUF_MODEL=PPTAgent
export PPT_CREATOR_AI_CTX_SIZE=8192
export PPT_CREATOR_AI_MAX_TOKENS=1800
export PPT_CREATOR_AI_GPU_LAYERS=-1
export PPT_CREATOR_AI_TEMPERATURE=0.2
export PPT_CREATOR_AI_TIMEOUT_SECONDS=180
```

Pré-requisito:

```bash
brew install llama.cpp
```

O provider local agora força modo **não conversacional** (`--no-conversation`) e `--simple-io` para evitar que o `llama-cli` fique preso esperando input interativo no final da geração. Se quiser guardar a saída bruta do modelo para debug:

Ele também passa a **preferir `llama-completion`** quando esse binário estiver disponível, porque algumas instalações locais do `llama.cpp` aceitam melhor o fluxo one-shot nele do que no `llama-cli`.

```bash
export PPT_CREATOR_AI_RAW_OUTPUT_PATH=outputs/pptagent_raw_output.txt
```

Os comandos da CLI agora também emitem logs mais claros com prefixos como:

- `[INFO]`
- `[OK]`
- `[WARN]`
- `[ERROR]`

Gerar previews PNG por slide e uma folha de thumbnails:

```bash
python -m ppt_creator.cli preview examples/ai_sales.json outputs/previews \
  --basename ai-sales-preview
```

Esse comando gera:

- um `.png` por slide
- uma folha `*-thumbnails.png` com miniaturas do deck
- um relatório heurístico de qualidade dentro do `--report-json`, quando usado

Você também pode ativar overlays de debug para inspecionar alinhamento e áreas seguras:

```bash
python -m ppt_creator.cli preview examples/ai_sales.json outputs/previews \
  --basename ai-sales-preview --debug-grid --debug-safe-areas
```

Isso ajuda a diagnosticar:

- safe areas
- header/body anchors
- linhas-guia de composição

Também existe agora uma seleção explícita de backend de preview:

```bash
python -m ppt_creator.cli preview examples/ai_sales.json outputs/previews \
  --backend auto
```

Opções disponíveis:

- `auto` → tenta usar backend Office quando disponível, com fallback para o sintético
- `synthetic` → força o preview em Pillow
- `office` → exige runtime compatível (`soffice`/`libreoffice`) para tentar previews mais fiéis ao `.pptx`

Hoje, se o runtime de Office não estiver instalado, o sistema cai automaticamente no backend sintético quando você usa `auto`.

A folha de thumbnails também começou a incorporar sinais do review heurístico, destacando slides mais arriscados com badges de risco e regiões prováveis de overflow.

Também entrou uma primeira camada de **regressão visual baseada em golden previews**:

```bash
python -m ppt_creator.cli preview examples/ai_sales.json outputs/previews \
  --baseline-dir outputs/golden-previews --write-diff-images
```

Isso permite comparar os previews atuais contra um diretório baseline, gerar scores de diferença por slide e opcionalmente salvar imagens de diff para inspeção.

Também já existe um caminho explícito para gerar preview a partir de um **`.pptx` real**:

```bash
python -m ppt_creator.cli preview-pptx outputs/ai_sales.pptx outputs/ai_sales_real_previews
```

Esse fluxo ajuda a aproximar ainda mais a inspeção visual do artefato final gerado.

Quando o LibreOffice exporta apenas um PNG único na conversão direta do `.pptx`, o projeto agora tenta automaticamente um caminho mais robusto:

- `.pptx` -> `.pdf` via LibreOffice
- `.pdf` -> um PNG por página via Ghostscript (`gs`)

Isso melhora bastante a confiabilidade do preview real em ambientes onde a exportação direta para PNG não sai slide a slide.

## Modo API / serviço

Também existe um modo HTTP simples para integrar o `ppt_creator` em outros fluxos:

```bash
python -m ppt_creator.api --host 127.0.0.1 --port 8787 --asset-root examples
```

Endpoints disponíveis:

- `GET /health`
- `GET /templates`
- `POST /review`
- `POST /preview`
- `POST /validate`
- `POST /render`
- `POST /template`

O endpoint `POST /render` também pode receber `include_review: true` para devolver a revisão heurística junto com o resultado do render/dry-run.

Exemplo de validação por API:

```bash
curl -X POST http://127.0.0.1:8787/template \
  -H 'Content-Type: application/json' \
  -d '{"domain":"sales"}'
```

---

## Como rodar com Docker

Build:

```bash
docker build -t ppt-creator .
```

Run com bind mount do diretório atual:

```bash
docker run --rm -v "$PWD:/work" ppt-creator \
  python -m ppt_creator.cli render /work/examples/ai_sales.json /work/outputs/ai_sales.pptx
```

Ou com helper:

```bash
bash bin/render_ppt_creator_docker.sh examples/ai_sales.json outputs/ai_sales.pptx
```

---

## Como gerar o deck de exemplo

```bash
python -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales.pptx
```

Saída esperada:

- arquivo `.pptx` real em `outputs/ai_sales.pptx`
- deck com 10 slides
- notas do apresentador por slide

Exemplos adicionais disponíveis:

- `examples/product_strategy.json`
- `examples/board_review.json`

Você também pode renderizar todos com:

```bash
make render-all-examples
```

---

## Testes

Executar testes rápidos:

```bash
pytest -q
```

Os testes cobrem:

- validação do schema
- renderização mínima de `.pptx`
- execução simples da CLI
- validação e renderização de todos os exemplos em `examples/`

---

## Productização e DX

O projeto agora também inclui:

- `CHANGELOG.md`
- `Makefile`
- workflow de CI em `.github/workflows/ci.yml`
- configuração de lint/format com Ruff no `pyproject.toml`

Importante: a lint/CI desta camada foi configurada para validar o **subprojeto de PPT**, e não todos os scripts legados do playground.

Comandos úteis:

```bash
make install-dev
make lint
make test
make validate-example
make render-example
make render-all-examples
```

---

## Reuso em outro projeto

Formas simples de reaproveitar:

1. copiar `ppt_creator/`, `pyproject.toml`, `Dockerfile` e `bin/`
2. instalar o pacote em outro diretório
3. montar JSONs compatíveis com o schema
4. gerar decks sem depender do restante do playground

Como o componente não está acoplado ao runtime de LLM, ele pode ser usado como etapa final de renderização em qualquer pipeline.

---

## Limitações atuais

- gráficos simples suportados, mas ainda sem visualização avançada/múltiplas configurações analíticas
- sem geração automática de conteúdo por LLM
- imagens são opcionais e não passam por tratamento avançado de crop/layout inteligente
- imagens ausentes usam um placeholder estruturado, mas ainda sem fallback visual avançado por tipo de conteúdo
- não usa templates `.potx` externos nesta primeira versão

---

## Próximos passos possíveis

- integração opcional com LLM para gerar JSON
- mais temas visuais e branding mais avançado
- gráficos e tabelas executivas
- sugestão automática de imagens
- suporte opcional a template externo premium

## Camada opcional de briefing estruturado

Exemplo de input opcional em `examples/briefing_sales.json`.

Essa camada tenta:

- gerar um deck inicial a partir de briefing
- expandir um outline em agenda e narrativa básica
- montar slides estruturados de contexto, métricas, timeline, comparação, FAQ e summary
- resumir texto mais longo em bullets executivos
- sugerir direções de imagem / placeholder automaticamente
- revisar densidade do deck gerado para sinalizar slides potencialmente carregados

Ela **não depende de LLM** nesta fase: é um gerador heurístico, útil como ponto de partida para pipelines futuros.

Para preparar a futura entrada de LLM real, a camada opcional agora já possui uma interface de provider. Hoje existe apenas o provider `heuristic`, mas a arquitetura foi organizada para receber providers futuros sem acoplar o núcleo do `ppt_creator`.

Ela agora já inclui tanto um provider local via GGUF/`llama.cpp` quanto um provider local via **Ollama**, permitindo experimentar modelos locais sem depender de APIs externas.

Também já existem providers remotos opcionais para **OpenAI** e **Anthropic**, mantendo a mesma interface de provider da camada opcional.

Além disso, a CLI dessa camada opcional já começa a suportar um primeiro fluxo mais próximo de pipeline completo, com geração, revisão e renderização em sequência.

## Evolução visual e QA

O projeto agora também começou a ganhar uma primeira camada de QA visual heurística no pipeline de previews:

- thumbnail sheet mais legível e organizado
- identificação visual de slide número/título/tipo
- overlays de debug opcionais
- revisão heurística de densidade e risco visual no relatório de preview
- comando/endpoint dedicado de review heurístico para QA do deck

Também começou a entrar uma primeira camada de **auto-fit tipográfico** em caixas homogêneas mais críticas, especialmente para reduzir overflow em títulos, subtitles, narrative boxes e painéis executivos mais sensíveis.

Essa cobertura inicial agora já alcança também mais layouts executivos com maior chance de overflow, como:

- `agenda`
- `metrics`
- `faq`
- `table`
- `image_text`

Também começou a entrar uma base bem inicial de **layout primitives** dentro do renderizador, com utilitários para:

- calcular bounds internos de painéis de forma consistente
- distribuir regiões verticais dentro de painéis compostos
- distribuir regiões horizontais para rows/columns de forma reutilizável
- compor grids simples a partir dessas regiões para layouts multi-painel
- expor helpers mais semânticos para `columns`, `rows`, `panel rows` e `panel grids`
- usar pesos de conteúdo para começar a balancear larguras e alturas automaticamente
- começar a aplicar stacks verticais guiadas por conteúdo em regiões textuais mais densas
- expandir esse balanceamento para layouts de agenda, bullets e closing com mais regiões semânticas

Essa base já começou a ser aplicada em layouts compostos mais exigentes, como:

- `comparison`
- `faq`
- `cards`
- `two_column`
- `metrics`
- `table`
- `summary`

Além disso, alguns layouts já começaram a ganhar um primeiro balanceamento automático baseado em densidade de conteúdo, especialmente em colunas/rows como `metrics`, `cards`, `table`, `comparison`, `two_column`, `faq` e `summary`.

Layouts narrativos com mistura de corpo + bullets, como `comparison`, `two_column` e `image_text`, também começaram a usar stacks verticais reequilibradas por peso de conteúdo para reduzir divisão rígida de espaço.

Essa mesma abordagem começou a se espalhar também para outros layouts executivos, como `agenda`, `bullets` e `closing`, que agora usam divisões mais semânticas e menos rígidas para texto, painéis e blocos auxiliares.

O rollout também já começou a alcançar layouts que ainda estavam mais rígidos, como `title`, `section`, `chart` e `timeline`, especialmente com splits ponderados, stacks internas mais semânticas e cobertura adicional de auto-fit em blocos sensíveis.

Isso ainda não é um layout engine completo, mas já é o primeiro passo para sair de coordenadas excessivamente rígidas e caminhar para composição mais resiliente.

Também já existe uma primeira infraestrutura para um backend de preview mais fiel ao `.pptx` quando um runtime de Office estiver disponível localmente, mantendo fallback limpo para o preview sintético.

Na camada de review heurístico, o projeto também começou a ganhar sinais mais fortes de **risco visual**, incluindo:

- contagem por severidade (`high` / `medium` / `low`)
- sinais agregados de risco de overflow
- sinais agregados de desbalanceamento entre painéis/colunas

Esses sinais ainda são heurísticos, mas ajudam a transformar o review em algo mais próximo de um QA de composição, não só de validação estrutural.

Os relatórios também passam a destacar melhor onde olhar primeiro, com campos como:

- `clipping_risk_count`
- `top_risk_slides`
- `likely_overflow_regions` por slide

O próximo passo mais importante continua sendo evoluir de preview sintético para preview fiel ao `.pptx` real.

Também entrou uma primeira camada de análise de artefatos no próprio preview, com sinais como contato com bordas e densidade suspeita nas margens do slide.

Também começou a entrar uma primeira camada de **crop/cover-fit mais inteligente** para imagens encaixadas em caixas fixas, especialmente no layout `image_text` e no preview correspondente, reduzindo distorção e melhorando o aproveitamento visual da área de imagem.
