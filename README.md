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

Os comandos da CLI agora também emitem logs mais claros com prefixos como:

- `[INFO]`
- `[OK]`
- `[WARN]`
- `[ERROR]`

## Modo API / serviço

Também existe um modo HTTP simples para integrar o `ppt_creator` em outros fluxos:

```bash
python -m ppt_creator.api --host 127.0.0.1 --port 8787 --asset-root examples
```

Endpoints disponíveis:

- `GET /health`
- `GET /templates`
- `POST /validate`
- `POST /render`
- `POST /template`

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
