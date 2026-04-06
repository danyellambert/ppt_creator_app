# NEXT STEPS — PPT Creator Roadmap

## Ajuste tático em andamento — host-native first com Docker service-first preparado

Objetivo desta trilha curta:

- consolidar o `ppt_creator_app` como renderer HTTP especializado do AI Workbench Local
- manter **host-native** como modo operacional recomendado agora
- deixar a imagem/container e o compose prontos para adoção futura sem refazer a arquitetura

### Checklist desta trilha

- [x] confirmar o `boundary` oficial: AI Workbench = domínio/orquestração, `ppt_creator_app` = renderer especializado
- [x] manter `GET /health`, `POST /render` e `GET /artifact` como contrato principal do P1 atual
- [x] formalizar `host-native` como operação recomendada de curto prazo
- [x] preparar Dockerfile para modo API service-first
- [x] adicionar `docker-compose.yml` para subir o serviço em `:8787`
- [x] adicionar helper/targets para `docker compose up --build`
- [x] documentar o fluxo para integração com o AI Workbench
- [ ] validar smoke test manual do caminho containerizado (`/health`, `/render`, `/artifact`, `/playground`)
- [ ] decidir quando o modo containerizado vira o default operacional

Este documento agora combina **duas coisas ao mesmo tempo**:

1. uma visão consolidada e atual do que ainda falta para o app ficar incrível
2. o **histórico preservado** das fases e entregas anteriores, sem apagar o que já foi feito

O bloco inicial abaixo mostra a leitura mais atual do projeto.
No final do arquivo existe um **anexo histórico preservado** com as fases anteriores e os acompanhamentos que já tinham sido construídos.

O `ppt_creator` já deixou de ser um MVP simples. Hoje ele já funciona como:

- motor Python de `JSON -> .pptx`
- CLI de validate / render / review / preview / compare
- API HTTP local com playground
- biblioteca de layouts executivos e temas prontos
- bloco reutilizável para pipelines
- camada opcional de briefing/IA desacoplada do renderizador base

O que falta agora não é “virar funcional”.

O que falta é o app ficar:

1. **visualmente impecável no artefato final**
2. **mais previsível em QA visual e regressão**
3. **mais fácil de usar no dia a dia**
4. **mais forte como produto reutilizável e distribuível**

---

## 1. Estado atual consolidado

Hoje o app já entrega:

- [x] schema com `pydantic`
- [x] renderização `.pptx` com `python-pptx`
- [x] speaker notes
- [x] CLI de validate / render / review / preview / compare
- [x] API HTTP local
- [x] playground local inicial
- [x] batch rendering
- [x] dry-run / reports / asset warnings
- [x] temas prontos (`executive_premium_minimal`, `consulting_clean`, `dark_boardroom`, `startup_minimal`)
- [x] branding básico por cor / logo / footer / client name
- [x] layouts executivos principais
- [x] workflows, audience profiles e asset collections iniciais
- [x] catálogo interno leve de temas / layouts / workflows / brand packs / assets / perfis
- [x] QA heurístico por slide e por deck
- [x] preview sintético e preview via runtime Office
- [x] comparação visual entre versões `.pptx`
- [x] Docker / Makefile / Ruff / CI / testes
- [x] camada opcional `ppt_creator_ai/` desacoplada do núcleo

### Layouts já suportados

- [x] `title`
- [x] `section`
- [x] `agenda`
- [x] `bullets`
- [x] `cards`
- [x] `metrics`
- [x] `chart`
- [x] `image_text`
- [x] `timeline`
- [x] `comparison`
- [x] `two_column`
- [x] `table`
- [x] `faq`
- [x] `summary`
- [x] `closing`

---

## 2. Entregas concluídas no ciclo atual

Este ciclo fechou uma parte importante do gap de **preview/regressão visual**:

- [x] gerar e salvar **manifesto de preview** com provenance do conjunto gerado
- [x] registrar no manifesto:
  - [x] `preview_source`
  - [x] `backend_requested`
  - [x] `backend_used`
  - [x] `office_conversion_strategy`
  - [x] arquivos e ordem dos slides
- [x] fazer regressão visual usar a **ordem do manifesto**, não só o `glob` de PNGs do diretório
- [x] expor metadados de provenance em relatórios de preview / compare
- [x] detectar e reportar **mismatch de provenance** entre baseline e current preview
- [x] adicionar flags de **require real preview** na CLI
- [x] adicionar suporte equivalente na API
- [x] adicionar testes cobrindo:
  - [x] manifesto de preview
  - [x] regressão usando manifesto
  - [x] falha quando preview real é obrigatório e não existe runtime Office
  - [x] compare de `.pptx` com provenance real
- [x] adicionar catálogo interno/marketplace leve via API/CLI para temas, layouts, perfis, workflows, brand packs e assets
- [x] adicionar trilha explícita de proposta/comercial com `domain=proposal`, `profile=proposal` e workflow `commercial_proposal`
- [x] consolidar helpers nomeados de layout e painéis estruturados reutilizáveis (`build_named_columns`, `build_named_rows`, `build_named_panel_row_content_bounds`, `build_named_panel_content_stack_bounds`, `add_structured_panel`) com adoção inicial em `title`, `section`, `summary` e `closing`
- [x] expandir focal point contextual/crop para `section` no renderer e no preview sintético correspondente
- [x] introduzir uma biblioteca leve de componentes visuais reutilizáveis (`ppt_creator/layouts/_components.py`) com adoção inicial em `metrics`, `cards` e `agenda`
- [x] reduzir coordenadas rígidas adicionais em layouts narrativos com splits/columns semânticos em `image_text` e `bullets`

---

## 3. O que ainda falta para o app ficar incrível

### Leitura curta e priorizada do que falta

Se a pergunta for **"o que realmente falta agora?"**, a resposta curta é esta:

#### Faltando agora

- [x] reduzir o retoque manual nos layouts mais sensíveis com um `visual slot` compartilhado, placeholders/crop mais consistentes e adoção prática em `section`, `image_text`, `summary` e `closing`
- [x] reduzir atrito do playground com foco automático no slide de maior risco e edição guiada de `image_path`, caption e focal point
- [x] consolidar primitives/constraints reutilizáveis com `add_accent_panel` e `add_visual_slot`
- [x] calibrar os exemplos e layouts principais até o corpus de referência sair com QA limpo e bem próximo de **zero retoque manual** no artefato final

#### Faltando depois

- [x] ampliar o QA para `section`, `cards`, `chart` e `image_text` com sinais explícitos e cobertura de teste
- [x] endurecer QA visual e regressão baseada no `.pptx` real como caminho operacional dominante
- [x] endurecer a camada AI opcional com repair loop, observabilidade, benchmarking entre providers/modelos e previsibilidade de saída
- [x] separar o backlog aspiracional em trilhas de expansão futura, sem tratar wishlist como bloqueio do core roadmap

#### Itens históricos que já podem ser tratados como arquivados

- [x] tudo que já está marcado como concluído nas prioridades principais deve ser lido como **feito e preservado por contexto**, não como trabalho ainda em aberto
- [x] itens antigos que falavam em **"primeira camada"**, quando já tiveram expansão e testes no ciclo atual, podem ser considerados encerrados no roadmap principal
- [x] temas mais aspiracionais como marketplace interno, biblioteca visual mais ampla e integrações operacionais/comerciais podem ficar como **wishlist / expansão futura**, e não como bloqueio para considerar o app excelente

## Prioridade 1 — Fidelidade visual final e QA de verdade

Esses são os itens de maior impacto percebido.

### 3.1. Preview e regressão visual

- [x] salvar manifesto de preview por execução
- [x] usar manifesto para ordenar/comparar previews
- [x] exigir preview real via CLI/API quando necessário
- [x] tornar o preview derivado do `.pptx` real o caminho **padrão recomendado** em toda a documentação e nos fluxos de regressão mais críticos
- [x] adicionar workflow explícito de **promote baseline** / refresh de golden previews
- [x] adicionar modo de **falha por regressão** para CI/pipeline (`fail on diff`)
- [x] destacar melhor nos relatórios:
  - [x] slides adicionados/removidos
  - [x] top diffs por severidade
  - [x] mismatch de provenance com guidance acionável
- [x] permitir comparação entre conjuntos com labels / metadata mais legíveis para debugging

### 3.2. Detectores visuais mais fortes

- [x] evoluir heurísticas para algo mais próximo de colisão/clipping real
- [x] detectar melhor:
  - [x] overflow em caixas compostas
  - [x] clipping perto de footer
  - [x] crowding em cantos e safe areas
  - [x] colisões entre blocos em layouts compostos
- [x] adicionar sinais mais fortes específicos para:
  - [x] `summary`
  - [x] `comparison`
  - [x] `two_column`
  - [x] `table`
  - [x] `faq`
  - [x] `metrics`

---

## Prioridade 2 — Polimento do motor de layout

O motor já está forte, mas ainda falta acabamento sistemático.

### 4.1. Rebalance e auto-fit em layouts compostos

- [x] criar um renderer compartilhado para famílias parecidas (`comparison` / `two_column`) para reduzir drift visual
- [x] adicionar uma segunda passada de rebalance quando o shrink de texto ficar agressivo
- [x] expandir auto-fit real para caixas compostas e painéis complexos
- [x] balancear melhor alturas e colunas em:
  - [x] `comparison`
  - [x] `two_column`
  - [x] `summary`
  - [x] `table`
  - [x] `faq`
  - [x] `metrics`
  - [x] `closing`

### 4.2. Baselines e anchors semânticos

- [x] formalizar baseline vertical por tipo de slide
- [x] formalizar anchors consistentes para:
  - [x] heading
  - [x] subtitle
  - [x] panel title
  - [x] body region
  - [x] footer boundary
- [x] reduzir pequenas variações de alinhamento entre layouts semelhantes

### 4.3. Revisão visual slide a slide

- [x] revisar detalhadamente `title`
- [x] revisar detalhadamente `metrics`
- [x] revisar detalhadamente `comparison`
- [x] revisar detalhadamente `two_column`
- [x] revisar detalhadamente `table`
- [x] revisar detalhadamente `faq`
- [x] revisar detalhadamente `summary`
- [x] revisar detalhadamente `closing`

---

## Prioridade 3 — Pipeline de imagens e placeholders

### 5.1. Crop e focal point

- [x] cover-fit/focal point inicial em `image_text`
- [x] expansão inicial para `title.hero_cover`
- [x] expandir crop/focal point para mais layouts com imagem
- [x] adicionar regras contextuais por tipo de slide para decidir melhor framing/crop

### 5.2. Placeholders mais premium

- [x] primeira evolução do placeholder estruturado
- [x] criar placeholders contextuais por tipo de slide
- [x] diferenciar melhor placeholder de:
  - [x] foto
  - [x] screenshot
  - [x] diagrama
  - [x] gráfico/visual analítico

### 5.3. Asset pipeline

- [x] brand packs reutilizáveis com logo/cor/footer/cover style
- [x] presets de assets visuais por domínio/workflow
- [x] sugestões mais contextuais de imagem por slide e narrativa

---

## Prioridade 4 — UX de criação e operação

Hoje o app é poderoso, mas ainda muito centrado em JSON.

### 6.1. Playground e fluxo de uso

- [x] playground local inicial
- [x] bootstrap por workflow/template/perfil
- [x] persistência local de estado no navegador
- [x] live preview / live review sem tanta fricção
- [x] UX melhor de “editar -> revisar -> ajustar -> exportar”
- [x] cards visuais para artifacts/reports no playground
- [x] erros de validação com foco mais acionável por campo/bloco
- [x] abrir e comparar versões do deck mais facilmente no playground

### 6.2. Editor visual leve

- [x] editor visual leve para os casos mais comuns
- [x] edição guiada de:
  - [x] title/subtitle/body
  - [x] bullets
  - [x] metrics
  - [x] comparison columns
  - [x] table rows
  - [x] FAQ items
- [x] sem substituir o JSON, mas reduzindo atrito para uso diário

---

## Prioridade 5 — Productização, distribuição e adoção

### 7.1. Release e distribuição

- [x] CI / lint / Makefile / changelog
- [x] pipeline de release formal
- [x] publicação consistente do pacote
- [x] estratégia de versionamento e releases mais operacional

### 7.2. Documentação e prova visual

- [x] README com galeria visual real de decks gerados
- [x] screenshots / exemplos visuais por layout
- [x] docs específicas para:
  - [x] preview provenance
  - [x] visual regression
  - [x] compare-pptx
  - [x] review-pptx
  - [x] baseline management
- [x] docs específicas para a camada AI opcional e seu boundary com o app
- [x] mais exemplos end-to-end por workflow real:
  - [x] sales QBR
  - [x] board strategy review
  - [x] product operating review
  - [x] consulting steerco

### 7.3. Posicionamento do produto

- [x] deixar mais explícito se o produto é:
  - [x] library
  - [x] CLI tool
  - [x] local service
  - [x] app com playground
- [x] documentar a arquitetura “core renderer vs AI service” de forma mais honesta e estável

---

## Prioridade 6 — Camada opcional de IA

IA continua opcional. O core deve seguir desacoplado.

### 8.1. O que já existe

- [x] provider heurístico
- [x] provider `local_service`
- [x] geração de deck estruturado a partir de briefing
- [x] review/refine/regenerate heurístico inicial
- [x] crítica slide a slide combinando sinais de QA

### 8.2. O que ainda falta

- [x] decidir e documentar melhor a fronteira do app:
  - [x] manter providers reais só atrás de `local_service`
  - [x] ou expor providers first-class no próprio app
- [x] hardening mais profundo de integrações reais
- [x] retries / timeout / structured errors melhores
- [x] reescrita executiva mais forte para slides fracos
- [x] loop iterativo com critério de parada mais claro:
  - [x] briefing
  - [x] geração
  - [x] render
  - [x] QA visual
  - [x] crítica
  - [x] revisão opcional
  - [x] nova iteração
- [x] exemplos e docs melhores da camada AI opcional

### 8.3. Direção decidida para prompts livres e providers model-backed

- [x] `ai_first` passa a ser o caminho principal para `intent_text` / prompt livre
- [x] a heurística não deve ser o caminho padrão quando o objetivo for autoria por IA
- [x] a heurística permanece como fallback de segurança, não como trajetória principal
- [x] quando `provider_name` não for informado em prompt livre, o app deve preferir um provider model-backed (`local_service` no backend)
- [x] no playground, providers model-backed devem aparecer como caminho preferencial de uso
- [x] `ollama_local` passa a existir como provider first-class no app
- [x] `ollama_local` precisa permitir listar modelos disponíveis e selecionar explicitamente um deles

Evoluções que ainda valem depois desta decisão:

- [x] medir a taxa de fallback heurístico por provider/modelo
- [x] benchmark comparativo entre `ollama_local` e `local_service` para prompts livres
- [x] endurecer ainda mais o repair loop antes do fallback heurístico

### 8.4. Hardening universal de qualidade AI sem overfitting por tipo de deck

Direção decidida para não perder o raciocínio:

- [x] priorizar **sinais universais de qualidade** em vez de hacks específicos para um único tipo de deck
- [x] evitar overfitting de entrevista / board / sales como solução principal
- [x] melhorar a qualidade por meio de **guardrails generalizáveis** de narrativa, evidência, consistência de idioma e anti-template leakage

Princípios universais que valem para muitos decks:

- [x] bloquear vazamento de scaffolding/template copy no output final
  - [x] evitar textos default como `Executive lens`, `What matters`, `Key takeaways`, `Next actions`, `Candidate Name`
  - [x] evitar labels técnicos/placeholder gritados no artefato final quando faltarem imagens
- [x] reforçar **specificity over template feel**
  - [x] títulos e bullets devem reutilizar o vocabulário do briefing
  - [x] claims fortes devem vir acompanhados de alguma forma de evidência
- [x] reforçar **evidence-bearing structures**
  - [x] quando houver claims de impacto/capacidade/valor, preferir métricas, chart, tabela, comparison, timeline, case cards ou detalhe operacional concreto
- [x] bloquear **pseudo-métricas qualitativas fracas**
  - [x] exemplos: `Alta`, `Otimizada`, `Contínua`, `Strong`, `Optimized`, `Accelerated`
- [x] manter consistência de idioma no output final
  - [x] se o briefing está em PT-BR, evitar rótulos soltos em inglês sem necessidade
- [x] pensar em arquétipos amplos de deck, não hacks estreitos
  - [x] decision deck
  - [x] review deck
  - [x] strategy deck
  - [x] profile/hiring deck
  - [x] proposal deck
  - [x] operating deck

Backlog derivado desta linha:

- [x] adicionar guardrails universais no contrato/prompt para anti-template leakage e consistência de idioma
- [x] endurecer o quality gate para detectar scaffolding copy e métricas qualitativas fracas
- [x] reduzir textos default do renderer que poluem o deck final
- [x] medir “specificity score” mais explicitamente no quality gate
- [x] medir “claim sem prova” de forma mais robusta
- [x] transformar os domínios atuais em arquétipos narrativos mais amplos e reaproveitáveis

Detalhamento do que entrou nesta iteração:

- [x] `specificity score` v1 baseado em cobertura ponderada de vocabulário do briefing no payload final
- [x] detecção v1 de `claim sem prova` considerando pressão de claims vs slides/strings com evidência
- [x] introdução de arquétipos narrativos amplos reutilizáveis:
  - [x] `decision`
  - [x] `review`
  - [x] `strategy`
  - [x] `profile`
  - [x] `proposal`
  - [x] `operating`

O que ainda pode evoluir depois disso:

- [x] calibrar thresholds do `specificity score` com benchmark maior por provider/modelo
- [x] sofisticar a detecção de `claim sem prova` para usar relações slide-a-slide e não só heurística textual/estrutural
- [x] usar arquétipos também no loop de refine/review para orientar regeneração e crítica

---

## 4. Ordem recomendada de execução daqui para frente

### Agora

1. tornar preview real / regressão visual mais oficial no pipeline
2. fortalecer detectores de clipping/collision/overflow
3. fazer polish dos layouts mais sensíveis

### Em seguida

4. melhorar playground e fluxo de edição/review/export
5. evoluir brand packs / assets / placeholders
6. melhorar docs visuais e prova de qualidade

### Depois

7. release/distribuição mais madura
8. editor visual leve
9. IA iterativa mais forte

---

## 5. Critério para considerar o app “incrível”

Podemos considerar que o app atingiu esse nível quando:

- [x] o preview/regressão usa o artefato final com confiança alta
- [x] os principais layouts saem quase sem retoque manual
- [x] o review aponta primeiro os slides realmente arriscados
- [x] o playground permite iteração rápida sem dor
- [x] novos decks podem ser gerados por template/workflow sem mexer em código
- [x] a documentação visual prova a qualidade do resultado
- [x] o app pode ser reutilizado como library, CLI ou service com pouco atrito

---

## 6. Próximo ciclo recomendado

Se o próximo ciclo for curto e de máximo impacto, a recomendação é:

### Sprint sugerida

1. `fail-on-regression` + baseline promotion workflow
2. detectores visuais mais fortes para preview final
3. polish de `comparison`, `two_column`, `summary` e `table`
4. README com galeria visual + docs de preview/regressão
5. melhorias de UX no playground para review/export

Esse é o caminho com maior chance de transformar o app de “forte tecnicamente” em **muito forte também na percepção de produto**.

---

## 7. Programa longo para fechar o backlog histórico remanescente

Os itens ainda abertos no anexo histórico **não são todos independentes**: parte deles é duplicação de itens-pai antigos, e parte é trabalho técnico real ainda não concluído.

Para atacar **literalmente tudo** de forma honesta, o caminho correto é este programa em etapas:

### Etapa 1 — Consolidação final do motor de layout

- consolidar primitives reutilizáveis de mais alto nível para `stack`, `grid`, `panel row` e composições mistas
- substituir mais coordenadas rígidas restantes por constraints/layout semântico
- criar stacks/rows/columns realmente reutilizáveis para reduzir drift entre layouts semelhantes
- fechar a lacuna restante entre primitives já existentes e uma biblioteca interna de composição mais uniforme

### Etapa 2 — Balanceamento, auto-fit e prevenção forte de overflow

- expandir balanceamento para regras mais fortes e consistentes em todo o sistema
- reforçar o balanceamento automático de alturas/colunas em todos os layouts compostos relevantes
- fechar os últimos gaps de auto-fit real por caixa/bloco nas regiões ainda mais frágeis
- adicionar prevenção mais forte de overflow visual antes da etapa final de preview

### Etapa 3 — Convergência total para preview/regressão do artefato real

- tornar a comparação baseada preferencialmente em preview do `.pptx` real o comportamento dominante em todos os fluxos históricos equivalentes
- eliminar ambiguidades restantes entre caminhos sintéticos e caminhos baseados no artefato final
- fechar os itens-pai históricos restantes de preview/regressão assim que a convergência estiver completa e comprovada

### Etapa 4 — Biblioteca visual e pipeline de imagem mais inteligente

- criar uma biblioteca de componentes visuais reutilizáveis acima dos helpers atuais
- expandir a estratégia de crop/focal point para mais layouts e regras contextuais
- evoluir “crop mais inteligente” de recurso pontual para comportamento sistêmico do renderer

### Etapa 5 — Expansão e hardening mais profundo da camada AI opcional

- adicionar providers/integrações adicionais quando houver boundary estável para isso
- endurecer ainda mais a infraestrutura de runtime/provider, observabilidade e previsibilidade operacional
- fechar o backlog histórico remanescente da camada AI sem misturar isso com o core renderer

### Critério de fechamento desse programa

Esse programa só deve ser considerado concluído quando:

- os itens-pai históricos restantes puderem ser marcados sem ambiguidade
- os itens técnicos remanescentes tiverem evidência em código + teste + comportamento real
- o anexo histórico puder ser lido mais como registro preservado do que como backlog ativo

---

## Anexo A — Histórico preservado do roadmap anterior

Este anexo preserva o conteúdo histórico do `NEXT_STEPS` anterior para que as fases já pensadas e o acompanhamento do que foi concluído **não se percam**.

---

### A.1. Estado do projeto na visão anterior

Na versão anterior do roadmap, o projeto já era entendido como uma base muito boa, com:

- módulo Python reutilizável
- CLI para validação e renderização
- schema com `pydantic`
- renderização `.pptx` com `python-pptx`
- tema inicial premium
- layouts principais de slides
- suporte a speaker notes
- exemplo funcional de deck
- Dockerfile
- testes rápidos

Leitura central daquela fase:

> já existia um **MVP técnico funcional**, e o foco passava a ser endurecer a base e elevar o nível de profissionalismo.

---

### A.2. Visão de produto preservada

Visão sugerida no roadmap anterior:

> Um renderizador de apresentações em Python, leve e desacoplado, capaz de transformar conteúdo estruturado em decks executivos visualmente consistentes, com qualidade suficiente para uso interno, consultivo e comercial.

Pontos de princípio preservados:

- o `ppt_creator` não precisa virar um framework gigante
- ele deve ser um **motor confiável de geração de decks**
- o JSON estruturado continua sendo a interface principal
- LLM/IA entra como camada opcional, não como dependência do núcleo

---

### A.3. Princípios de qualidade preservados

#### Engenharia

- API simples e previsível
- baixo acoplamento
- testes rápidos e confiáveis
- versionamento claro
- comportamento reprodutível

#### Design

- consistência entre slides
- sistema de tokens claro
- layouts equilibrados
- boa hierarquia tipográfica
- qualidade visual sem depender de assets proprietários

#### Produto

- fácil de rodar localmente
- fácil de rodar via Docker
- fácil de copiar para outro projeto
- documentação objetiva
- exemplos reais e úteis
- escopo claro e independente do playground legado

#### Operação

- mensagens de erro boas
- inputs válidos e inválidos bem tratados
- outputs previsíveis
- fácil automação em pipeline

---

### A.4. Roadmap histórico por fases

## Fase 0 — Hardening do MVP

Objetivo histórico: deixar a base estável, limpa e pronta para crescer.

#### Status preservado

- [x] normalizar nomes de tema e campos textuais no schema
- [x] melhorar mensagens de erro da CLI
- [x] validar arquivo de entrada inexistente com erro claro
- [x] validar extensão de saída `.pptx`
- [x] adicionar testes rápidos para validações e erros comuns
- [x] revisar a API pública do pacote
- [x] padronizar nomes de funções, classes e arquivos
- [x] adicionar testes de regressão mínimos para todos os layouts
- [x] documentar melhor limitações restantes da Fase 0

#### Entregas preservadas

- [x] revisar a API pública do pacote
- [x] padronizar nomes de funções, classes e arquivos
- [x] revisar mensagens de erro da CLI
- [x] melhorar validações do schema
- [x] revisar tratamento de caminhos de imagem e output
- [x] adicionar testes de regressão mínimos para cada layout
- [x] documentar melhor limitações conhecidas

#### Itens concretos preservados

- [x] garantir comportamento consistente entre tipos de slide
- [x] validar limites úteis por tipo de conteúdo
  - [x] quantidade máxima recomendada de bullets
  - [x] quantidade esperada de métricas
  - [x] campos obrigatórios por tipo
- [x] melhorar o fallback de imagem ausente
- [x] revisar geração de notes para evitar edge cases
- [x] padronizar strings de tema e nomes internos

Resultado histórico esperado: o projeto deixava de ser “protótipo promissor” e passava a ser um **MVP sólido**.

---

## Fase 1 — Design System de verdade

Objetivo histórico: elevar a qualidade visual e tornar o tema realmente reutilizável.

#### Status preservado

- [x] expandir tokens com grupos de spacing e components
- [x] criar primeiras variantes de layout reutilizáveis
- [x] formalizar grid/layout base de forma mais abrangente
- [x] criar helpers adicionais para blocos visuais recorrentes
- [x] revisar proporções e alinhamentos slide a slide

#### Entregas preservadas

- [x] expandir tokens visuais
- [x] formalizar grid/layout base
- [x] criar regras consistentes de spacing
- [x] criar componentes visuais reutilizáveis
- [x] reduzir diferenças visuais entre layouts

#### Itens concretos preservados

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
- [x] criar variantes para layouts-chave
  - [x] bullets: “left text / right insight” e “full-width bullets”
  - [x] metrics: “3 KPIs” e “4 KPIs compactos”
  - [x] image_text: “image right” e “image left”

Resultado histórico esperado: o projeto ganhava um **design system interno real**.

#### Aprofundamento de design/layout preservado

- [x] substituir coordenadas mais rígidas por primitives de layout e constraints semânticas
  - [x] primeira primitive utilitária para bounds internos de painéis e distribuição vertical de regiões
  - [x] primeira aplicação dessas primitives em layouts compostos (`comparison`, `faq`, `cards`, `two_column`)
  - [x] distribuição horizontal reutilizável para rows/columns, aplicada em `metrics`, `cards` e `table`
  - [x] composição simples de grids multi-painel aplicada em `comparison`, `two_column`, `faq` e `summary`
  - [x] primeiros helpers mais semânticos reaproveitados em múltiplos layouts
  - [x] expandir primitives para stacks/rows/columns semânticos de uso geral
  - [x] primeira stack vertical guiada por conteúdo aplicada em regiões narrativas mistas
  - [x] expansão inicial dessas stacks/weights para `agenda`, `bullets` e `closing`
  - [x] primeira expansão adicional para `title`, `section`, `chart` e `timeline`
  - [x] primeira camada explícita de constraints semânticas com `target_share`, `max_width` e `max_height`
  - [x] expandir stacks semânticas reutilizáveis para mais layouts e regiões internas
  - [x] consolidar helpers nomeados de layout/painel estruturado para reduzir wiring manual de bounds em layouts reais
- [x] criar stacks/rows/columns reutilizáveis para reduzir desalinhamentos entre layouts
  - [x] primeira camada prática de APIs nomeadas para columns/rows/panel rows aplicada em layouts executivos reais
  - [x] nova adoção em layouts narrativos (`agenda`, `bullets`, `image_text`) reduzindo drift de composição entre famílias semelhantes
- [x] adicionar auto-fit tipográfico e controle de overflow por bloco
  - [x] primeira camada de auto-fit em títulos, subtitles e caixas homogêneas críticas
  - [x] expansão inicial para layouts com maior risco de overflow (`agenda`, `metrics`, `faq`, `table`, `image_text`)
  - [x] expansão adicional para `title`, `section`, `chart` e `timeline`
  - [x] expandir auto-fit para todos os layouts e blocos compostos
- [x] balancear melhor colunas, cards e painéis quando o conteúdo variar
  - [x] primeira camada de balanceamento adaptativo por peso de conteúdo em layouts executivos chave
  - [x] avanço adicional com panel-grids/rows constrained em `metrics`, `comparison`, `faq` e `summary`
  - evolução futura preservada: expandir balanceamento para heurísticas ainda mais fortes e consistentes em todo o sistema
- [x] formalizar baseline vertical e anchors consistentes por tipo de slide
- [x] revisar visualmente, slide a slide, `title`, `metrics`, `comparison`, `table`, `faq`, `summary` e `closing`

---

## Fase 2 — Productização e experiência de desenvolvedor

Objetivo histórico: fazer o projeto parecer e funcionar como uma ferramenta séria.

#### Status preservado

- [x] definir estratégia inicial de versionamento semântico
- [x] criar `CHANGELOG.md`
- [x] adicionar `Makefile` com comandos principais
- [x] adicionar lint/format com Ruff
- [x] configurar CI simples
- [x] adicionar mais exemplos de entrada
- [x] melhorar README com fluxos de uso e DX
- [x] restringir lint/CI ao escopo do subprojeto `ppt_creator`

#### Entregas preservadas

- [x] empacotamento melhor
- [x] versionamento formal
- [x] changelog
- [x] automação de qualidade
- [x] documentação de uso mais forte

#### Itens concretos preservados

- [x] definir estratégia de versionamento semântico
- [x] criar `CHANGELOG.md`
- [x] adicionar `Makefile` com comandos curtos
  - [x] `make install`
  - [x] `make test`
  - [x] `make render-example`
  - [x] `make docker-render`
- [x] adicionar lint/format com Ruff
- [x] configurar CI simples para instalar dependências, rodar testes e validar exemplo JSON
- [x] melhorar README com fluxos de uso
- [x] adicionar mais exemplos de entrada
- [x] explicitar o escopo da productização no subprojeto `ppt_creator`

Resultado histórico esperado: qualquer pessoa conseguiria clonar, instalar, testar e usar o projeto com muito menos atrito.

---

## Fase 3 — Expansão funcional útil

Objetivo histórico: aumentar a utilidade prática para uso executivo real.

#### Entregas preservadas

- novos tipos de slide
- branding configurável
- mais flexibilidade sem perder simplicidade

#### Funcionalidades candidatas já concluídas

- [x] tabela executiva
- [x] agenda / roadmap slide
- [x] timeline
- [x] comparison slide
- [x] two-column narrative slide
- [x] FAQ / appendix slide
- [x] summary slide final
- [x] cover variants

#### Branding e configuração preservados

- permitir configuração simples por JSON ou arquivo de tema:
  - [x] cor principal
  - [x] cor secundária
  - [x] logo opcional
  - [x] nome do cliente
  - [x] rodapé customizado
- preparar suporte a múltiplos temas:
  - [x] `executive_premium_minimal`
  - [x] `consulting_clean`
  - [x] `dark_boardroom`
  - [x] `startup_minimal`

Resultado histórico esperado: o `ppt_creator` deixava de ser um gerador para caso único e passava a ser uma **plataforma leve de decks executivos**.

---

## Fase 4 — Robustez para uso em pipeline

Objetivo histórico: preparar o projeto para uso recorrente e embutido em fluxos maiores.

#### Entregas preservadas

- execução batch
- validação mais forte
- outputs auxiliares
- previsibilidade operacional

#### Itens concretos preservados

- [x] suportar renderização em lote
- [x] emitir logs mais claros
- [x] adicionar modo `--check` / `--dry-run`
- [x] gerar relatório simples de renderização
- [x] validar assets ausentes com warnings úteis
- [x] suportar diretórios de input/output configuráveis
- [x] permitir templates de deck por domínio
  - [x] vendas
  - [x] consultoria
  - [x] estratégia
  - [x] produto

#### Bloco prioritário histórico de pipeline visual

- [x] melhorar a folha de thumbnails com composição mais legível e metadados por slide
- [x] adicionar overlays opcionais de debug para grid e safe areas no preview sintético
- [x] adicionar revisão heurística inicial de qualidade visual no relatório de preview
- [x] enriquecer a thumbnail sheet com sinais de risco vindos do review heurístico
- [x] expor revisão heurística dedicada via CLI/API para QA do deck
- [x] reaproveitar revisão heurística em relatórios de preview e render/dry-run
- [x] preparar seleção de backend com tentativa de preview via runtime Office e fallback limpo para o sintético

##### Preview real / regressão — histórico preservado

- [x] gerar preview a partir do `.pptx` real em vez de reconstrução paralela em Pillow
  - [x] primeiro fluxo explícito de preview a partir de `.pptx` real via CLI/API
  - [x] fallback mais robusto quando o Office não exporta um PNG por slide diretamente (`.pptx` -> `.pdf` -> PNG por página)
  - [x] integração inicial desse caminho ao fluxo principal de render, preferindo o artefato final quando possível
  - [x] camada opcional de geração/preview passou a preferir automaticamente o `.pptx` final em mais cenários
  - [x] evoluir para usar isso como caminho preferencial em mais cenários de QA/regressão
  - [x] primeiro fluxo explícito de review QA direto sobre `.pptx` renderizado
- [x] adicionar regressão visual baseada em previews reais/golden files
  - [x] primeira camada de comparação contra golden previews com diffs opcionais
  - [x] caminhos opcionais com `render-pptx` + baseline passaram a favorecer preview real quando disponível
  - [x] primeiro fluxo dedicado para comparar duas versões `.pptx` via previews reais e diff automático
  - [x] evoluir para comparação baseada preferencialmente em preview do `.pptx` real
- [x] criar detectores mais fortes de colisão, overflow e clipping
  - [x] primeira camada heurística de risco de overflow e desbalanceamento exposta no review/QA
  - [x] sumarização de slides mais arriscados e sinais de clipping/overflow em relatórios de QA
  - [x] primeira análise de artefatos no próprio preview (edge contact / edge density)
  - [x] nova camada de sinais baseados no corpo útil do preview (safe-area intrusion, footer-boundary crowding, unsafe corner density)
  - [x] primeira camada de sinais de layout-pressure/collision aproximando regiões reais de composição por tipo de slide
  - [x] evoluir para detectores mais próximos de colisão/clipping real com base em preview/layout final

Resultado histórico esperado: o projeto ficava pronto para funcionar como **bloco de infraestrutura** dentro de outros sistemas.

---

## Fase 5 — Camada inteligente opcional

Objetivo histórico: adicionar inteligência sem acoplar o núcleo ao LLM.

#### Direção importante preservada

O núcleo do projeto deveria continuar sendo:

> conteúdo estruturado -> renderização consistente -> `.pptx`

Qualquer camada de IA deveria continuar opcional.

#### Possibilidades e avanços preservados

- [x] gerar JSON inicial a partir de briefing estruturado
- [x] expandir outline em slides estruturados
- [x] sugerir títulos, bullets e KPIs iniciais a partir do briefing
- [x] resumir texto longo em conteúdo executivo
- [x] sugerir imagens ou placeholders automáticos
- [x] revisar densidade de conteúdo por slide
- [x] usar LLM para revisão iterativa de narrativa após o primeiro deck ser gerado
- [x] usar LLM para reescrever títulos, subtitles e summaries em tom mais executivo
- [x] usar LLM para crítica slide a slide combinando briefing + QA visual
  - [x] primeira crítica slide a slide heurística derivada do review/QA nos relatórios da camada AI
  - [x] evoluir para crítica via LLM combinando briefing + QA visual

#### Providers e integrações preservados

- [x] provider local GGUF via `llama.cpp` para experimentar com `PPTAgent`
- [x] provider local via `Ollama`
- [x] providers remotos iniciais via `OpenAI` e `Anthropic`
- [x] endurecer execução local em modo não interativo com timeout e captura opcional de saída bruta
- [x] adaptar payloads alternativos do PPTAgent local para o schema canônico do `ppt_creator`
- evolução futura preservada: providers adicionais e hardening mais profundo de cada integração

#### Roadmap IA ainda aberto no histórico

- [x] geração de outline e narrativa a partir de briefing livre
- [x] reescrita executiva de conteúdo fraco
- [x] revisão iterativa do deck após renderização e QA
- [x] manter um loop mais forte: briefing -> estrutura -> render -> QA -> revisão opcional -> nova iteração
  - [x] primeira integração prática de generate + review + render dentro da CLI opcional de briefing
  - [x] primeira iteração automática heurística de refine/re-review na CLI opcional
  - [x] integração inicial de preview visual no pipeline opcional de briefing
  - [x] integração inicial de preview derivado do `.pptx` renderizado no pipeline opcional de briefing
  - [x] primeira regeneração automática baseada em feedback heurístico do review
  - [x] primeira incorporação de feedback vindo também do preview visual ao loop heurístico opcional
  - [x] evoluir para revisão opcional/regeração iterativa automática mais forte

Resultado histórico esperado: o projeto passava a ter potencial de **copiloto de criação de decks**, sem comprometer a simplicidade do núcleo.

---

### A.5. Ordem recomendada de execução preservada

#### Prioridade alta

1. **Fase 0 — Hardening do MVP**
2. **Fase 1 — Design System de verdade**
3. **Fase 2 — Productização e DX**

#### Prioridade média

4. **Fase 3 — Expansão funcional útil**
5. **Fase 4 — Robustez para pipeline**

#### Prioridade futura

6. **Fase 5 — Camada inteligente opcional**

---

### A.6. Top 10 melhorias de maior impacto preservadas

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

### A.7. Sinais preservados de que o projeto virou “muito profissional”

- novos decks são criados sem mexer no código-fonte
- o visual fica consistente em apresentações diferentes
- o schema impede a maioria dos erros comuns
- o projeto roda localmente e via Docker sem fricção
- os testes cobrem o núcleo de forma confiável
- a documentação permite reuso em outro projeto sem explicação verbal adicional
- novos temas e layouts podem ser adicionados sem refatorar o núcleo

---

### A.8. Backlog estratégico preservado

- [x] exportar preview PNG por slide
- [x] gerar thumbnails automáticos do deck
- [x] suportar gráficos simples gerados por dados
- [x] suportar tabelas executivas com estilo consistente
- [x] biblioteca de componentes visuais reutilizáveis
- [x] marketplace interno de temas/layouts
- [x] integração com workflow de propostas/comercial
- [x] modo API/serviço
- [x] editor visual futuro para montar JSON com menos fricção

#### Plano exaustivo de melhoria de máximo impacto preservado

##### Prioridade 1 — Fidelidade de preview e QA visual

- [x] preview gerado a partir do `.pptx`/PDF real
- [x] thumbnail sheet mais forte para inspeção visual
- [x] overlays de debug para analisar composição
- [x] revisão heurística inicial de qualidade
- [x] comparação visual automática entre versões

##### Prioridade 2 — Refatoração do motor de layout

- [x] primitives de layout (`stack`, `grid`, `two-column`, `panel row`)
  - [x] primeira base utilitária para inner bounds e distribuição vertical de regiões
  - [x] primeira aplicação em layouts compostos já existentes
  - [x] primeira distribuição horizontal reutilizável aplicada em rows/columns executivos
  - [x] primeira composição simples de grids aplicada em layouts multi-painel
  - [x] primeiros helpers semânticos de mais alto nível reaproveitados em layouts reais
  - [x] consolidar primitives reutilizáveis de mais alto nível
  - [x] primeira consolidação prática com constrained columns/rows em capas, seções, charts e timelines
  - [x] primeira expansão com helpers semânticos adicionais para panel-grid ponderado e panel-content stacks reutilizáveis
  - [x] nova expansão prática com constrained panel grids/rows em layouts compostos adicionais
  - [x] nova consolidação prática com helpers nomeados e painéis estruturados reutilizáveis em múltiplos layouts
- [x] constraints semânticas em vez de posições excessivamente rígidas
- [x] auto-fit real de texto por caixa
  - [x] primeira camada aplicada em caixas homogêneas críticas
  - [x] expansão inicial para layouts executivos com risco maior de densidade/overflow
  - [x] expansão para caixas compostas, grids e painéis complexos
- [x] balanceamento automático de alturas e colunas
  - [x] primeira camada guiada por peso de conteúdo em layouts executivos chave
  - evolução futura preservada: expandir para regras ainda mais fortes e consistentes em todo o sistema
- [x] prevenção mais forte de overflow visual

##### Prioridade 3 — Polimento visual por layout

- [x] revisão detalhada de `title`
- [x] revisão detalhada de `metrics`
- [x] revisão detalhada de `comparison` e `two_column`
- [x] revisão detalhada de `table`
- [x] revisão detalhada de `faq`
- [x] revisão detalhada de `summary` e `closing`

##### Prioridade 4 — Pipeline de imagens e placeholders

- [x] crop mais inteligente
  - [x] primeira camada de cover-fit/crop aplicada a caixas fixas de imagem (`image_text` + preview correspondente)
  - [x] primeira camada de focal point explícito (`image_focal_x` / `image_focal_y`) no render e no preview de slides com imagem
  - [x] primeira expansão da estratégia para além de `image_text`, aplicada a `title.hero_cover`
  - [x] nova expansão contextual para `section`, incluindo focal point no preview sintético correspondente
  - [x] expandir a estratégia para mais layouts e regras de focal point/contexto
- [x] placeholders mais premium e contextuais
  - [x] primeira evolução visual do placeholder estruturado em `image_text`
- [x] sugestões de imagem por tipo de slide, não só por briefing geral
  - [x] primeira camada de sugestões mais granulares por slide/tipo na análise heurística de briefing
  - [x] evoluir para sugestões mais contextuais com focal point/asset style
- [x] biblioteca básica de assets e estilos visuais

##### Prioridade 5 — LLM opcional de conteúdo e revisão

- [x] provider layer para múltiplas LLMs
- [x] provider local GGUF via `llama.cpp` para experimentar com `PPTAgent`
- [x] geração de outline e narrativa a partir de briefing livre
- [x] reescrita executiva de conteúdo fraco
- [x] revisão iterativa do deck após renderização e QA

##### Prioridade 6 — Produto / experiência de uso

- [x] editor visual leve
- [x] playground local para gerar/editar/re-renderizar decks
- [x] playground local mais robusto com bootstrap de template/perfil e controles operacionais básicos
- [x] perfis de público (board, consulting, sales, product)
- [x] integração com workflows comerciais e operacionais
  - [x] primeira biblioteca de workflow presets operacionais/comerciais com bootstrap via CLI/API
  - [x] playground local agora consegue carregar workflows e expor artefatos/previews de forma mais operacional

---

### A.9. Sugestão prática de próximo ciclo preservada

Sprint sugerida no roadmap anterior:

1. endurecer schema e CLI
2. refinar os layouts atuais visualmente
3. adicionar CI + lint/format
4. criar 2 exemplos novos
5. adicionar 2 novos tipos de slide muito úteis

---

### A.10. Resumo executivo preservado

- **primeiro**: consolidar o que já existe
- **depois**: elevar a qualidade visual e estrutural
- **em seguida**: transformar em ferramenta fácil de usar e manter
- **só depois**: expandir temas, layouts e inteligência opcional

Mensagem estratégica preservada:

> fortalecer o núcleo, formalizar o design system, productizar o uso e só então expandir.