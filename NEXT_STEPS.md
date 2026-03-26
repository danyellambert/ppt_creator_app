# NEXT STEPS — PPT Creator Roadmap

Este documento organiza os próximos passos para transformar o `ppt_creator` de um gerador funcional de `.pptx` em um componente **muito profissional, reutilizável, confiável e útil em contexto real de produto**.

O objetivo não é só “adicionar features”, mas evoluir o projeto em cinco dimensões:

1. **qualidade visual**
2. **qualidade de engenharia**
3. **reutilização em outros projetos**
4. **experiência de uso e operação**
5. **potencial de produto futuro**

---

## 1. Estado atual

Hoje o projeto já possui uma base muito boa:

- módulo Python reutilizável
- CLI para validação e renderização
- schema com `pydantic`
- renderização `.pptx` com `python-pptx`
- tema inicial `Executive Premium Minimal`
- layouts principais de slides
- suporte a speaker notes
- exemplo funcional de deck
- Dockerfile
- testes rápidos

Ou seja: **já existe um MVP técnico funcional**.

O próximo passo é endurecer essa base e elevá-la para um nível mais profissional.

---

## 2. Visão de produto

Visão sugerida para o projeto:

> Um renderizador de apresentações em Python, leve e desacoplado, capaz de transformar conteúdo estruturado em decks executivos visualmente consistentes, com qualidade suficiente para uso interno, consultivo e comercial.

Em outras palavras:

- o `ppt_creator` não precisa ser um “framework gigante”
- ele deve ser um **motor confiável de geração de decks**
- o JSON estruturado é a interface principal
- o LLM pode entrar depois, mas como camada opcional

---

## 3. Princípios para deixar o projeto muito profissional

Antes das fases, vale explicitar os critérios de qualidade desejados.

### 3.1. Engenharia

- API simples e previsível
- baixo acoplamento
- testes rápidos e confiáveis
- versionamento claro
- comportamento reprodutível

### 3.2. Design

- consistência entre slides
- sistema de tokens claro
- layouts equilibrados
- boa hierarquia tipográfica
- qualidade visual sem depender de assets proprietários

### 3.3. Produto

- fácil de rodar localmente
- fácil de rodar via Docker
- fácil de copiar para outro projeto
- documentação objetiva
- exemplos reais e úteis
- escopo claro e independente do playground legado

### 3.4. Operação

- mensagens de erro boas
- inputs válidos e inválidos bem tratados
- outputs previsíveis
- fácil automação em pipeline

---

## 4. Roadmap por fases

## Fase 0 — Hardening do MVP

Objetivo: deixar a base atual estável, limpa e pronta para crescer.

### Status de acompanhamento

- [x] normalizar nomes de tema e campos textuais no schema
- [x] melhorar mensagens de erro da CLI
- [x] validar arquivo de entrada inexistente com erro claro
- [x] validar extensão de saída `.pptx`
- [x] adicionar testes rápidos para validações e erros comuns
- [x] revisar a API pública do pacote
- [x] padronizar nomes de funções, classes e arquivos
- [x] adicionar testes de regressão mínimos para todos os layouts
- [x] documentar melhor limitações restantes da Fase 0

### Entregas

- [x] revisar a API pública do pacote
- [x] padronizar nomes de funções, classes e arquivos
- [x] revisar mensagens de erro da CLI
- [x] melhorar validações do schema
- [x] revisar tratamento de caminhos de imagem e output
- [x] adicionar testes de regressão mínimos para cada layout
- [x] documentar melhor limitações conhecidas

### Itens concretos

- [x] garantir que todos os tipos de slide tenham comportamento consistente
- [x] validar limites úteis, por exemplo:
  - [x] quantidade máxima recomendada de bullets
  - [x] quantidade esperada de métricas
  - [x] campos obrigatórios por tipo
- [x] melhorar o fallback de imagem ausente
- [x] revisar geração de notes para evitar edge cases
- [x] padronizar strings de tema e nomes internos

### Resultado esperado

Ao fim dessa fase, o projeto deixa de ser “protótipo promissor” e vira um **MVP sólido**.

---

## Fase 1 — Design System de verdade

Objetivo: elevar muito a qualidade visual e tornar o tema realmente reutilizável.

### Status de acompanhamento

- [x] expandir tokens com grupos de spacing e components
- [x] criar primeiras variantes de layout reutilizáveis
- [x] formalizar grid/layout base de forma mais abrangente
- [x] criar helpers adicionais para blocos visuais recorrentes
- [x] revisar proporções e alinhamentos slide a slide

### Entregas

- [x] expandir tokens visuais
- [x] formalizar grid/layout base
- [x] criar regras consistentes de spacing
- [x] criar componentes visuais reutilizáveis
- [x] reduzir diferenças visuais entre layouts

### Itens concretos

- [x] separar melhor tokens de:
  - [x] cores
  - [x] tipografia
  - [x] spacing
  - [x] grid
  - [x] cards
  - [x] métricas
  - [x] imagem/placeholder
- [x] definir áreas seguras por slide
- [x] criar helpers para:
  - [x] título padrão
  - [x] eyebrow padrão
  - [x] footer padrão
  - [x] painéis/cartões padrão
  - [x] blocos de quote
- [x] revisar proporções e alinhamentos slide a slide
- [x] criar pelo menos 2 variantes por alguns layouts
  - [x] bullets: “left text / right insight” e “full-width bullets”
  - [x] metrics: “3 KPIs” e “4 KPIs compactos”
  - [x] image_text: “image right” e “image left”

### Resultado esperado

Ao fim dessa fase, o projeto ganha um **design system interno real**, não só um conjunto de layouts isolados.

---

## Fase 2 — Productização e experiência de desenvolvedor

Objetivo: fazer o projeto parecer e funcionar como uma ferramenta séria.

### Status de acompanhamento

- [x] definir estratégia inicial de versionamento semântico
- [x] criar `CHANGELOG.md`
- [x] adicionar `Makefile` com comandos principais
- [x] adicionar lint/format com Ruff
- [x] configurar CI simples
- [x] adicionar mais exemplos de entrada
- [x] melhorar README com fluxos de uso e DX
- [x] restringir lint/CI ao escopo do subprojeto `ppt_creator`

### Entregas

- [x] empacotamento melhor
- [x] versionamento formal
- [x] changelog
- [x] automação de qualidade
- [x] documentação de uso mais forte

### Itens concretos

- [x] definir estratégia de versionamento semântico
- [x] criar `CHANGELOG.md`
- [x] adicionar `Makefile` com comandos curtos, por exemplo:
  - [x] `make install`
  - [x] `make test`
  - [x] `make render-example`
  - [x] `make docker-render`
- [x] adicionar lint/format, por exemplo:
  - [x] `ruff`
  - [x] formatação com `ruff format`
- [x] configurar CI simples para:
  - [x] instalar dependências
  - [x] rodar testes
  - [x] validar exemplo JSON
- [x] melhorar README com screenshots/exportações futuras
- [x] adicionar mais exemplos de entrada
- [x] deixar explícito que a productização cobre o subprojeto `ppt_creator`, não todos os scripts legados do playground

### Resultado esperado

Ao fim dessa fase, qualquer pessoa consegue clonar, instalar, testar e usar o projeto com muito menos atrito.

---

## Fase 3 — Expansão funcional útil

Objetivo: aumentar utilidade prática para uso executivo real.

### Entregas

- novos tipos de slide
- branding configurável
- mais flexibilidade sem perder simplicidade

### Funcionalidades candidatas

- tabela executiva
- agenda / roadmap slide
- timeline
- comparison slide
- two-column narrative slide
- FAQ / appendix slide
- summary slide final
- cover variants

### Branding e configuração

- permitir configuração simples por JSON ou arquivo de tema:
  - cor principal
  - cor secundária
  - logo opcional
  - nome do cliente
  - rodapé customizado
- preparar suporte a múltiplos temas:
  - `executive_premium_minimal`
  - `consulting_clean`
  - `dark_boardroom`
  - `startup_minimal` (se fizer sentido no futuro)

### Resultado esperado

Ao fim dessa fase, o `ppt_creator` deixa de ser apenas um gerador para um caso específico e vira uma **plataforma leve de decks executivos**.

---

## Fase 4 — Robustez para uso em pipeline

Objetivo: preparar o projeto para ser embutido em fluxos maiores e uso recorrente.

### Entregas

- execução batch
- validação mais forte
- outputs auxiliares
- previsibilidade operacional

### Itens concretos

- suportar renderização em lote
- emitir logs mais claros
- adicionar modo `--check` ou `--dry-run`
- gerar relatório simples de renderização
- validar assets ausentes com warnings úteis
- suportar diretórios de input/output configuráveis
- permitir templates de deck por domínio
  - vendas
  - consultoria
  - estratégia
  - produto

### Resultado esperado

Ao fim dessa fase, o projeto fica pronto para funcionar como **bloco de infraestrutura** dentro de outros sistemas.

---

## Fase 5 — Camada inteligente opcional

Objetivo: adicionar inteligência sem acoplar o núcleo ao LLM.

### Direção importante

O núcleo do projeto deve continuar sendo:

> conteúdo estruturado -> renderização consistente -> `.pptx`

Qualquer camada de IA deve ser opcional.

### Possibilidades futuras

- gerar JSON inicial a partir de briefing
- expandir outline em slides estruturados
- sugerir títulos, bullets e KPIs
- resumir texto longo em conteúdo executivo
- sugerir imagens ou placeholders automáticos
- revisar densidade de conteúdo por slide

### Arquitetura recomendada

- manter um módulo separado, algo como `ppt_creator_ai/` ou `pipelines/`
- nunca misturar lógica de prompt com o renderizador base
- tratar LLM como produtor de estrutura, não como renderizador

### Resultado esperado

Ao fim dessa fase, o projeto passa a ter potencial de **copiloto de criação de decks**, mas sem comprometer a simplicidade do núcleo.

---

## 5. Ordem recomendada de execução

Se a ideia for maximizar valor com esforço razoável, esta é a ordem recomendada:

### Prioridade alta

1. **Fase 0 — Hardening do MVP**
2. **Fase 1 — Design System de verdade**
3. **Fase 2 — Productização e DX**

### Prioridade média

4. **Fase 3 — Expansão funcional útil**
5. **Fase 4 — Robustez para pipeline**

### Prioridade futura

6. **Fase 5 — Camada inteligente opcional**

---

## 6. O que mais aumentaria o profissionalismo rapidamente

Se fosse necessário escolher poucos itens com maior impacto imediato, eu priorizaria estes:

### Top 10 melhorias de maior impacto

1. refinar visual e grid dos slides atuais
2. criar mais testes por layout
3. melhorar documentação de input JSON
4. adicionar CI
5. adicionar lint/format
6. criar 2 ou 3 exemplos adicionais de deck
7. suportar branding simples por tema/config
8. adicionar novos layouts executivos essenciais
9. melhorar fallback de imagens
10. criar um fluxo de release/versionamento

---

## 7. Sinais de que o projeto virou “muito profissional”

Você pode considerar que o projeto chegou num nível muito forte quando:

- novos decks são criados sem mexer no código-fonte
- o visual fica consistente em apresentações diferentes
- o schema impede a maioria dos erros comuns
- o projeto roda localmente e via Docker sem fricção
- os testes cobrem o núcleo de forma confiável
- a documentação permite reuso em outro projeto sem explicação verbal adicional
- novos temas e layouts podem ser adicionados sem refatorar o núcleo

---

## 8. Backlog estratégico de médio/longo prazo

Ideias valiosas, mas não urgentes:

- exportar preview PNG por slide
- gerar thumbnails automáticos do deck
- suportar gráficos simples gerados por dados
- suportar tabelas executivas com estilo consistente
- biblioteca de componentes visuais reutilizáveis
- marketplace interno de temas/layouts
- integração com workflow de propostas/comercial
- modo API/serviço
- editor visual futuro para montar JSON com menos fricção

---

## 9. Sugestão prática de próximo ciclo

Se o próximo ciclo for curto e objetivo, eu recomendo este pacote:

### Sprint recomendada

1. endurecer schema e CLI
2. refinar os layouts atuais visualmente
3. adicionar CI + lint/format
4. criar 2 exemplos novos
5. adicionar 2 novos tipos de slide muito úteis

Isso já deixaria o projeto com cara bem mais profissional sem exagerar no escopo.

---

## 10. Resumo executivo

Resumo simples do roadmap:

- **primeiro**: consolidar o que já existe
- **depois**: elevar a qualidade visual e estrutural
- **em seguida**: transformar em ferramenta fácil de usar e manter
- **só depois**: expandir temas, layouts e inteligência opcional

O maior risco neste tipo de projeto é pular cedo demais para features “inteligentes” e deixar a base visual/técnica inconsistente.

A melhor estratégia é:

> fortalecer o núcleo, formalizar o design system, productizar o uso e só então expandir.
