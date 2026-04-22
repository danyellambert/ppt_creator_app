# NEXT STEPS — PPT Creator Roadmap

## Tactical adjustment in progress — host-native first with Docker service-first ready

Objective of this short track:

- consolidate `ppt_creator_app` as the specialized HTTP renderer for AI Workbench Local
- keep **host-native** as the recommended operational mode for now
- leave the image/container and compose ready for future adoption without redesigning the architecture

### Checklist for this track

- [x] confirm the official `boundary`: AI Workbench = domain/orchestration, `ppt_creator_app` = specialized renderer
- [x] keep `GET /health`, `POST /render`, and `GET /artifact` as the main contract for the current P1
- [x] formalize `host-native` as the recommended short-term operating mode
- [x] prepare the Dockerfile for API service-first mode
- [x] add `docker-compose.yml` to bring the service up on `:8787`
- [x] add helpers/targets for `docker compose up --build`
- [x] document the integration flow with AI Workbench
- [ ] validate a manual smoke test for the containerized path (`/health`, `/render`, `/artifact`, `/playground`)
- [ ] decide when containerized mode becomes the operational default

This document now combines **two things at the same time**:

1. a consolidated, current view of what is still missing for the app to become amazing
2. the **preserved history** of previous phases and deliveries, without erasing what has already been done

The opening block below shows the most current reading of the project.
At the end of the file there is a **preserved historical appendix** with the earlier phases and tracking that had already been built.

`ppt_creator` is no longer a simple MVP. Today it already works as:

- a Python `JSON -> .pptx` engine
- a CLI for validate / render / review / preview / compare
- a local HTTP API with playground
- a library of executive layouts and ready-made themes
- a reusable block for pipelines
- an optional briefing/AI layer decoupled from the base renderer

What is missing now is not “becoming functional.”

What is missing is for the app to become:

1. **visually impeccable in the final artifact**
2. **more predictable in visual QA and regression**
3. **easier to use day to day**
4. **stronger as a reusable and distributable product**

---

## 1. Consolidated current state

Today the app already delivers:

- [x] schema with `pydantic`
- [x] `.pptx` rendering with `python-pptx`
- [x] speaker notes
- [x] validate / render / review / preview / compare CLI
- [x] local HTTP API
- [x] initial local playground
- [x] batch rendering
- [x] dry-run / reports / asset warnings
- [x] ready-made themes (`executive_premium_minimal`, `consulting_clean`, `dark_boardroom`, `startup_minimal`)
- [x] basic branding by color / logo / footer / client name
- [x] main executive layouts
- [x] initial workflows, audience profiles, and asset collections
- [x] lightweight internal catalog of themes / layouts / workflows / brand packs / assets / profiles
- [x] heuristic QA per slide and per deck
- [x] synthetic preview and preview via Office runtime
- [x] visual comparison between `.pptx` versions
- [x] Docker / Makefile / Ruff / CI / tests
- [x] optional `ppt_creator_ai/` layer decoupled from the core

### Layouts already supported

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

## 2. Deliveries completed in the current cycle

This cycle closed an important part of the **preview / visual regression** gap:

- [x] generate and save a **preview manifest** with provenance for the generated set
- [x] record in the manifest:
  - [x] `preview_source`
  - [x] `backend_requested`
  - [x] `backend_used`
  - [x] `office_conversion_strategy`
  - [x] slide files and ordering
- [x] make visual regression use the **manifest order**, not only the directory PNG `glob`
- [x] expose provenance metadata in preview / compare reports
- [x] detect and report **provenance mismatch** between baseline and current preview
- [x] add **require real preview** flags to the CLI
- [x] add equivalent support in the API
- [x] add tests covering:
  - [x] preview manifest
  - [x] regression using the manifest
  - [x] failure when real preview is required and no Office runtime exists
  - [x] `.pptx` compare with real provenance
- [x] add a lightweight internal catalog/marketplace via API/CLI for themes, layouts, profiles, workflows, brand packs, and assets
- [x] add an explicit proposal/commercial track with `domain=proposal`, `profile=proposal`, and workflow `commercial_proposal`
- [x] consolidate named layout helpers and reusable structured-panel helpers (`build_named_columns`, `build_named_rows`, `build_named_panel_row_content_bounds`, `build_named_panel_content_stack_bounds`, `add_structured_panel`) with initial adoption in `title`, `section`, `summary`, and `closing`
- [x] expand contextual focal point / crop to `section` in the renderer and in the corresponding synthetic preview
- [x] introduce a lightweight reusable visual component library (`ppt_creator/layouts/_components.py`) with initial adoption in `metrics`, `cards`, and `agenda`
- [x] reduce additional rigid coordinates in narrative layouts with semantic splits/columns in `image_text` and `bullets`

---

## 3. What is still missing for the app to become amazing

### Short, prioritized reading of what is missing

If the question is **"what is really missing right now?"**, the short answer is this:

#### Missing right now

- [x] reduce manual touch-up in the most sensitive layouts with a shared `visual slot`, more consistent placeholders/crop, and practical adoption in `section`, `image_text`, `summary`, and `closing`
- [x] reduce playground friction with automatic focus on the highest-risk slide and guided editing of `image_path`, caption, and focal point
- [x] consolidate reusable primitives/constraints with `add_accent_panel` and `add_visual_slot`
- [x] calibrate the main examples and layouts until the reference corpus comes out with clean QA and very close to **zero manual touch-up** in the final artifact

#### Missing later

- [x] expand QA for `section`, `cards`, `chart`, and `image_text` with explicit signals and test coverage
- [x] harden visual QA and regression based on the real `.pptx` as the dominant operational path
- [x] harden the optional AI layer with a repair loop, observability, provider/model benchmarking, and output predictability
- [x] separate the aspirational backlog into future-expansion tracks without treating wishlist items as blockers for the core roadmap

#### Historical items that can already be treated as archived

- [x] everything already marked as complete in the main priorities should be read as **done and preserved for context**, not as still-open work
- [x] older items that spoke about a **"first layer"**, when they have already been expanded and tested in the current cycle, can be considered closed in the main roadmap
- [x] more aspirational themes such as the internal marketplace, broader visual library, and operational/commercial integrations can remain as **wishlist / future expansion**, not as blockers to consider the app excellent

## Priority 1 — Final visual fidelity and real QA

These are the items with the highest perceived impact.

### 3.1. Preview and visual regression

- [x] save a preview manifest per run
- [x] use the manifest to order/compare previews
- [x] require real preview via CLI/API when needed
- [x] make preview derived from the real `.pptx` the **recommended default path** across the documentation and in the most critical regression flows
- [x] add an explicit **promote baseline** / golden preview refresh workflow
- [x] add a **fail on regression** mode for CI/pipeline (`fail on diff`)
- [x] highlight better in reports:
  - [x] added/removed slides
  - [x] top diffs by severity
  - [x] provenance mismatch with actionable guidance
- [x] allow comparison between sets with more readable labels / metadata for debugging

### 3.2. Stronger visual detectors

- [x] evolve heuristics toward something closer to real collision/clipping
- [x] improve detection of:
  - [x] overflow in composed boxes
  - [x] clipping near the footer
  - [x] crowding in corners and safe areas
  - [x] collisions between blocks in composed layouts
- [x] add stronger layout-specific signals for:
  - [x] `summary`
  - [x] `comparison`
  - [x] `two_column`
  - [x] `table`
  - [x] `faq`
  - [x] `metrics`

---

## Priority 2 — Layout engine polish

The engine is already strong, but it still lacks systematic finish.

### 4.1. Rebalance and auto-fit in composed layouts

- [x] create a shared renderer for similar families (`comparison` / `two_column`) to reduce visual drift
- [x] add a second rebalance pass when text shrink becomes too aggressive
- [x] expand real auto-fit to composed boxes and complex panels
- [x] balance heights and columns better in:
  - [x] `comparison`
  - [x] `two_column`
  - [x] `summary`
  - [x] `table`
  - [x] `faq`
  - [x] `metrics`
  - [x] `closing`

### 4.2. Baselines and semantic anchors

- [x] formalize a vertical baseline by slide type
- [x] formalize consistent anchors for:
  - [x] heading
  - [x] subtitle
  - [x] panel title
  - [x] body region
  - [x] footer boundary
- [x] reduce small alignment variations across similar layouts

### 4.3. Slide-by-slide visual review

- [x] review `title` in detail
- [x] review `metrics` in detail
- [x] review `comparison` in detail
- [x] review `two_column` in detail
- [x] review `table` in detail
- [x] review `faq` in detail
- [x] review `summary` in detail
- [x] review `closing` in detail

---

## Priority 3 — Image pipeline and placeholders

### 5.1. Crop and focal point

- [x] initial cover-fit/focal point in `image_text`
- [x] initial expansion to `title.hero_cover`
- [x] expand crop/focal point to more image-based layouts
- [x] add contextual rules by slide type to decide framing/crop better

### 5.2. More premium placeholders

- [x] first evolution of the structured placeholder
- [x] create contextual placeholders by slide type
- [x] differentiate placeholders more clearly for:
  - [x] photo
  - [x] screenshot
  - [x] diagram
  - [x] chart / analytical visual

### 5.3. Asset pipeline

- [x] reusable brand packs with logo/color/footer/cover style
- [x] visual asset presets by domain/workflow
- [x] more contextual image suggestions by slide and narrative

---

## Priority 4 — Creation and operations UX

Today the app is powerful, but still too centered on JSON.

### 6.1. Playground and usage flow

- [x] initial local playground
- [x] bootstrap by workflow/template/profile
- [x] local browser state persistence
- [x] live preview / live review with less friction
- [x] better UX for “edit -> review -> adjust -> export”
- [x] visual cards for artifacts/reports in the playground
- [x] validation errors with a more actionable focus by field/block
- [x] open and compare deck versions more easily in the playground

### 6.2. Lightweight visual editor

- [x] lightweight visual editor for the most common cases
- [x] guided editing of:
  - [x] title/subtitle/body
  - [x] bullets
  - [x] metrics
  - [x] comparison columns
  - [x] table rows
  - [x] FAQ items
- [x] without replacing JSON, but reducing friction for daily use

---

## Priority 5 — Productization, distribution, and adoption

### 7.1. Release and distribution

- [x] CI / lint / Makefile / changelog
- [x] formal release pipeline
- [x] consistent package publishing
- [x] more operational versioning and release strategy

### 7.2. Documentation and visual proof

- [x] README with a real visual gallery of generated decks
- [x] screenshots / visual examples by layout
- [x] specific docs for:
  - [x] preview provenance
  - [x] visual regression
  - [x] compare-pptx
  - [x] review-pptx
  - [x] baseline management
- [x] specific docs for the optional AI layer and its boundary with the app
- [x] more end-to-end examples by real workflow:
  - [x] sales QBR
  - [x] board strategy review
  - [x] product operating review
  - [x] consulting steerco

### 7.3. Product positioning

- [x] make it clearer whether the product is a:
  - [x] library
  - [x] CLI tool
  - [x] local service
  - [x] app with playground
- [x] document the “core renderer vs AI service” architecture more honestly and more stably

---

## Priority 6 — Optional AI layer

AI remains optional. The core should remain decoupled.

### 8.1. What already exists

- [x] heuristic provider
- [x] `local_service` provider
- [x] structured deck generation from a briefing
- [x] initial heuristic review/refine/regenerate flow
- [x] slide-by-slide critique combining QA signals

### 8.2. What was still missing

- [x] decide and document the app boundary more clearly:
  - [x] keep real providers only behind `local_service`
  - [x] or expose first-class providers in the app itself
- [x] deeper hardening of real integrations
- [x] better retries / timeout / structured errors
- [x] stronger executive rewriting for weak slides
- [x] a more explicit iterative loop with a clearer stopping criterion:
  - [x] briefing
  - [x] generation
  - [x] render
  - [x] visual QA
  - [x] critique
  - [x] optional revision
  - [x] new iteration
- [x] better examples and docs for the optional AI layer

### 8.3. Decided direction for free prompts and model-backed providers

- [x] `ai_first` becomes the main path for `intent_text` / free prompt
- [x] heuristics should not be the default path when Prethe goal is AI authorship
- [x] heuristics remain a safety fallback, not the primary trajectory
- [x] when `provider_name` is not informed for a free prompt, the app should prefer a model-backed provider (`local_service` on the backend)
- [x] in the playground, model-backed providers should appear as the preferred path
- [x] `ollama_local` now exists as a first-class provider in the app
- [x] `ollama_local` must allow listing available models and explicitly selecting one of them

Evolutions that still matter after this decision:

- [x] measure heuristic fallback rate by provider/model
- [x] comparative benchmark between `ollama_local` and `local_service` for free prompts
- [x] harden the repair loop even further before heuristic fallback

### 8.4. Universal AI quality hardening without overfitting by deck type

Decided direction so the reasoning is not lost:

- [x] prioritize **universal quality signals** instead of hacks for a single deck type
- [x] avoid overfitting interview / board / sales as the main solution
- [x] improve quality through **generalizable guardrails** for narrative, evidence, language consistency, and anti-template leakage

Universal principles that apply to many decks:

- [x] block scaffolding/template-copy leakage in the final output
  - [x] avoid default text like `Executive lens`, `What matters`, `Key takeaways`, `Next actions`, `Candidate Name`
  - [x] avoid loud technical/placeholder labels in the final artifact when images are missing
- [x] reinforce **specificity over template feel**
  - [x] titles and bullets should reuse the vocabulary of the briefing
  - [x] strong claims should be accompanied by some form of evidence
- [x] reinforce **evidence-bearing structures**
  - [x] when there are claims of impact/capability/value, prefer metrics, chart, table, comparison, timeline, case cards, or concrete operational detail
- [x] block **weak qualitative pseudo-metrics**
  - [x] examples: `High`, `Optimized`, `Continuous`, `Strong`, `Accelerated`
- [x] keep output language consistent
  - [x] if the briefing is in PT-BR, avoid stray English labels unless truly needed
- [x] think in terms of broad deck archetypes, not narrow hacks
  - [x] decision deck
  - [x] review deck
  - [x] strategy deck
  - [x] profile/hiring deck
  - [x] proposal deck
  - [x] operating deck

Derived backlog from this direction:

- [x] add universal guardrails in the contract/prompt for anti-template leakage and language consistency
- [x] harden the quality gate to detect scaffolding copy and weak qualitative metrics
- [x] reduce renderer default text that pollutes the final deck
- [x] measure “claim without proof” more robustly
- [x] transform the current domains into broader, more reusable narrative archetypes

Details of what entered in this iteration:

- [x] `specificity score` v1 based on weighted coverage of briefing vocabulary in the final payload
- [x] v1 detection of `claim without proof` considering claim pressure vs slides/strings with evidence
- [x] introduction of broad reusable narrative archetypes:
  - [x] `decision`
  - [x] `review`
  - [x] `strategy`
  - [x] `profile`
  - [x] `proposal`
  - [x] `operating`

What can still evolve after that:

- [x] calibrate `specificity score` thresholds with a larger benchmark by provider/model
- [x] make `claim without proof` detection more sophisticated using slide-to-slide relationships, not only textual/structural heuristics
- [x] use archetypes in the refine/review loop as well to guide regeneration and critique

---

## 4. Recommended execution order from here forward

### Now

1. make real preview / visual regression more official in the pipeline
2. strengthen clipping/collision/overflow detectors
3. polish the most sensitive layouts

### Next

4. improve the playground and the edit/review/export flow
5. evolve brand packs / assets / placeholders
6. improve visual docs and proof of quality

### Later

7. more mature release/distribution
8. lightweight visual editor
9. stronger iterative AI

---

## 5. Criterion for considering the app “amazing”

We can consider the app to have reached that level when:

- [x] preview/regression uses the final artifact with high confidence
- [x] the main layouts come out with almost no manual touch-up
- [x] review surfaces the truly risky slides first
- [x] the playground enables fast iteration without pain
- [x] new decks can be generated by template/workflow without touching code
- [x] the visual documentation proves output quality
- [x] the app can be reused as a library, CLI, or service with low friction

---

## 6. Recommended next cycle

If the next cycle is short and aimed at maximum impact, the recommendation is:

### Suggested sprint

1. `fail-on-regression` + baseline-promotion workflow
2. stronger visual detectors for final preview
3. polish `comparison`, `two_column`, `summary`, and `table`
4. README with visual gallery + preview/regression docs
5. UX improvements in the playground for review/export

This is the path with the best chance of turning the app from “technically strong” into **very strong in product perception too**.

---

## 7. Long program to close the remaining historical backlog

The items still open in the historical appendix **are not all independent**: part of them duplicates older parent items, and part is real technical work that is not yet completed.

To tackle **literally everything** honestly, the correct path is this staged program:

### Stage 1 — Final consolidation of the layout engine

- consolidate higher-level reusable primitives for `stack`, `grid`, `panel row`, and mixed compositions
- replace more of the remaining rigid coordinates with semantic constraints/layout
- create truly reusable stacks/rows/columns to reduce drift between similar layouts
- close the remaining gap between already existing primitives and a more uniform internal composition library

### Stage 2 — Balancing, auto-fit, and strong overflow prevention

- expand balancing into stronger, more consistent rules across the whole system
- reinforce automatic balancing of heights/columns across all relevant composed layouts
- close the last gaps in real box/block auto-fit in the most fragile remaining regions
- add stronger visual overflow prevention before the final preview stage

### Stage 3 — Full convergence to real-artifact preview/regression

- make comparison based preferentially on preview from the real `.pptx` the dominant behavior in all equivalent historical flows
- eliminate remaining ambiguities between synthetic paths and final-artifact-based paths
- close the remaining historical parent items for preview/regression as soon as convergence is complete and proven

### Stage 4 — Visual library and smarter image pipeline

- create a library of reusable visual components above the current helpers
- expand the crop/focal-point strategy to more layouts and contextual rules
- evolve “smarter crop” from a point feature into systemic renderer behavior

### Stage 5 — Deeper expansion and hardening of the optional AI layer

- add more providers/integrations when a stable boundary exists for that
- harden runtime/provider infrastructure, observability, and operational predictability even further
- close the remaining historical backlog of the AI layer without mixing it with the core renderer

### Criterion for closing this program

This program should only be considered complete when:

- the remaining historical parent items can be marked without ambiguity
- the remaining technical items have evidence in code + tests + real behavior
- the historical appendix can be read more as a preserved record than as an active backlog

---

## Appendix A — Preserved history of the previous roadmap

This appendix preserves the historical content of the previous `NEXT_STEPS` so that the phases that had already been envisioned and the tracking of what was completed **are not lost**.

---

### A.1. Project state in the previous view

In the previous version of the roadmap, the project was already understood as a very good foundation, with:

- reusable Python module
- CLI for validation and rendering
- schema with `pydantic`
- `.pptx` rendering with `python-pptx`
- initial premium theme
- main slide layouts
- speaker notes support
- a functional deck example
- Dockerfile
- fast tests

Main takeaway from that phase:

> there was already a **functional technical MVP**, and the focus then shifted to hardening the foundation and raising the level of professionalism.

---

### A.2. Preserved product vision

Vision suggested in the previous roadmap:

> A lightweight, decoupled presentation renderer in Python, capable of turning structured content into visually consistent executive decks, with enough quality for internal, consulting, and commercial use.

Preserved guiding points:

- `ppt_creator` does not need to become a giant framework
- it should be a **reliable deck-generation engine**
- structured JSON remains the main interface
- LLM/AI enters as an optional layer, not as a core dependency

---

### A.3. Preserved quality principles

#### Engineering

- simple, predictable API
- low coupling
- fast and reliable tests
- clear versioning
- reproducible behavior

#### Design

- consistency across slides
- clear token system
- balanced layouts
- good typographic hierarchy
- visual quality without depending on proprietary assets

#### Product

- easy to run locally
- easy to run via Docker
- easy to copy into another project
- objective documentation
- real and useful examples
- clear scope independent of the legacy playground

#### Operations

- good error messages
- valid and invalid inputs handled well
- predictable outputs
- easy pipeline automation

---

### A.4. Historical roadmap by phases

## Phase 0 — MVP hardening

Historical objective: make the foundation stable, clean, and ready to grow.

#### Preserved status

- [x] normalize theme names and text fields in the schema
- [x] improve CLI error messages
- [x] validate nonexistent input file with a clear error
- [x] validate `.pptx` output extension
- [x] add fast tests for validations and common errors
- [x] review the package public API
- [x] standardize function, class, and file names
- [x] add minimum regression tests for all layouts
- [x] better document remaining Phase 0 limitations

#### Preserved deliverables

- [x] review the package public API
- [x] standardize function, class, and file names
- [x] review CLI error messages
- [x] improve schema validation
- [x] review handling of image and output paths
- [x] add minimum regression tests for each layout
- [x] better document known limitations

#### Preserved concrete items

- [x] ensure consistent behavior across slide types
- [x] validate useful limits by content type
  - [x] recommended maximum bullet count
  - [x] expected metric count
  - [x] required fields by type
- [x] improve missing-image fallback
- [x] review notes generation to avoid edge cases
- [x] standardize theme strings and internal names

Expected historical outcome: the project stopped being a “promising prototype” and became a **solid MVP**.

---

## Phase 1 — A real design system

Historical objective: raise visual quality and make the theme truly reusable.

#### Preserved status

- [x] expand tokens with spacing groups and components
- [x] create the first reusable layout variants
- [x] formalize the base grid/layout more broadly
- [x] create additional helpers for recurring visual blocks
- [x] review proportions and alignment slide by slide

#### Preserved deliverables

- [x] expand visual tokens
- [x] formalize the base grid/layout
- [x] create consistent spacing rules
- [x] create reusable visual components
- [x] reduce visual differences between layouts

#### Preserved concrete items

- [x] separate tokens more clearly for:
  - [x] colors
  - [x] typography
  - [x] spacing
  - [x] grid
  - [x] cards
  - [x] metrics
  - [x] image/placeholder
- [x] define safe areas per slide
- [x] create helpers for:
  - [x] default title
  - [x] default eyebrow
  - [x] default footer
  - [x] default panels/cards
  - [x] quote blocks
- [x] review proportions and alignment slide by slide
- [x] create variants for key layouts
  - [x] bullets: “left text / right insight” and “full-width bullets”
  - [x] metrics: “3 KPIs” and “4 compact KPIs”
  - [x] image_text: “image right” and “image left”

Expected historical outcome: the project gained a **real internal design system**.

#### Preserved design/layout deepening

- [x] replace more rigid coordinates with layout primitives and semantic constraints
  - [x] first utility primitive for panel inner bounds and vertical distribution of regions
  - [x] first application of those primitives in composed layouts (`comparison`, `faq`, `cards`, `two_column`)
  - [x] reusable horizontal distribution for rows/columns, applied in `metrics`, `cards`, and `table`
  - [x] simple multi-panel grid composition applied in `comparison`, `two_column`, `faq`, and `summary`
  - [x] first higher-level semantic helpers reused across multiple layouts
  - [x] expand primitives to semantic stacks/rows/columns for general use
  - [x] first content-guided vertical stack applied in mixed narrative regions
  - [x] initial expansion of those stacks/weights to `agenda`, `bullets`, and `closing`
  - [x] first additional expansion to `title`, `section`, `chart`, and `timeline`
  - [x] first explicit semantic-constraint layer with `target_share`, `max_width`, and `max_height`
  - [x] expand reusable semantic stacks to more layouts and internal regions
  - [x] consolidate named layout / structured-panel helpers to reduce manual bounds wiring in real layouts
- [x] create reusable stacks/rows/columns to reduce misalignment across layouts
  - [x] first practical layer of named APIs for columns/rows/panel rows applied in real executive layouts
  - [x] new adoption in narrative layouts (`agenda`, `bullets`, `image_text`) reducing composition drift across similar families
- [x] add typographic auto-fit and overflow control by block
  - [x] first auto-fit layer in titles, subtitles, and critical homogeneous boxes
  - [x] initial expansion to layouts with higher overflow risk (`agenda`, `metrics`, `faq`, `table`, `image_text`)
  - [x] additional expansion to `title`, `section`, `chart`, and `timeline`
  - [x] expand auto-fit to all layouts and composed blocks
- [x] balance columns, cards, and panels better when content varies
  - [x] first layer of adaptive balancing by content weight in key executive layouts
  - [x] additional progress with constrained panel-grids/rows in `metrics`, `comparison`, `faq`, and `summary`
  - future evolution preserved: expand balancing to even stronger, more consistent heuristics across the system
- [x] formalize vertical baselines and consistent anchors by slide type
- [x] visually review, slide by slide, `title`, `metrics`, `comparison`, `table`, `faq`, `summary`, and `closing`

---

## Phase 2 — Productization and developer experience

Historical objective: make the project look and work like a serious tool.

#### Preserved status

- [x] define an initial semantic versioning strategy
- [x] create `CHANGELOG.md`
- [x] add `Makefile` with main commands
- [x] add lint/format with Ruff
- [x] configure simple CI
- [x] add more input examples
- [x] improve the README with usage flows and DX
- [x] restrict lint/CI to the `ppt_creator` subproject scope

#### Preserved deliverables

- [x] better packaging
- [x] formal versioning
- [x] changelog
- [x] quality automation
- [x] stronger usage documentation

#### Preserved concrete items

- [x] define semantic versioning strategy
- [x] create `CHANGELOG.md`
- [x] add `Makefile` with short commands
  - [x] `make install`
  - [x] `make test`
  - [x] `make render-example`
  - [x] `make docker-render`
- [x] add lint/format with Ruff
- [x] configure simple CI to install dependencies, run tests, and validate a JSON example
- [x] improve the README with usage flows
- [x] add more input examples
- [x] make the scope of productization explicit in the `ppt_creator` subproject

Expected historical outcome: anyone could clone, install, test, and use the project with far less friction.

---

## Phase 3 — Useful functional expansion

Historical objective: increase practical usefulness for real executive use.

#### Preserved deliverables

- new slide types
- configurable branding
- more flexibility without losing simplicity

#### Candidate features already completed

- [x] executive table
- [x] agenda / roadmap slide
- [x] timeline
- [x] comparison slide
- [x] two-column narrative slide
- [x] FAQ / appendix slide
- [x] final summary slide
- [x] cover variants

#### Preserved branding and configuration

- allow simple configuration via JSON or theme file:
  - [x] primary color
  - [x] secondary color
  - [x] optional logo
  - [x] client name
  - [x] custom footer
- prepare support for multiple themes:
  - [x] `executive_premium_minimal`
  - [x] `consulting_clean`
  - [x] `dark_boardroom`
  - [x] `startup_minimal`

Expected historical outcome: `ppt_creator` stopped being a single-case generator and became a **lightweight executive deck platform**.

---

## Phase 4 — Robustness for pipeline use

Historical objective: prepare the project for recurring use and for embedding in larger flows.

#### Preserved deliverables

- batch execution
- stronger validation
- auxiliary outputs
- operational predictability

#### Preserved concrete items

- [x] support batch rendering
- [x] emit clearer logs
- [x] add `--check` / `--dry-run` mode
- [x] generate a simple render report
- [x] validate missing assets with useful warnings
- [x] support configurable input/output directories
- [x] allow domain-based deck templates
  - [x] sales
  - [x] consulting
  - [x] strategy
  - [x] product

#### Preserved historical priority block for the visual pipeline

- [x] improve the thumbnail sheet with more readable composition and per-slide metadata
- [x] add optional debug overlays for grid and safe areas in the synthetic preview
- [x] add initial heuristic visual-quality review in the preview report
- [x] enrich the thumbnail sheet with risk signals coming from heuristic review
- [x] expose dedicated heuristic review via CLI/API for deck QA
- [x] reuse heuristic review in preview reports and render/dry-run reports
- [x] prepare backend selection with Office-runtime preview attempts and clean fallback to synthetic preview

##### Real preview / regression — preserved history

- [x] generate preview from the real `.pptx` instead of a parallel reconstruction in Pillow
  - [x] first explicit flow for preview from real `.pptx` via CLI/API
  - [x] more robust fallback when Office does not export one PNG per slide directly (`.pptx` -> `.pdf` -> PNG per page)
  - [x] initial integration of that path into the main render flow, preferring the final artifact whenever possible
  - [x] optional generation/preview layer began automatically preferring the final `.pptx` in more scenarios
  - [x] evolve this into the preferred path in more QA/regression scenarios
  - [x] first explicit QA review flow directly on rendered `.pptx`
- [x] add visual regression based on real previews / golden files
  - [x] first layer of comparison against golden previews with optional diffs
  - [x] optional `render-pptx` + baseline paths began favoring real preview when available
  - [x] first dedicated flow to compare two `.pptx` versions via real previews and automatic diff
  - [x] evolve toward preferential comparison based on preview from the real `.pptx`
- [x] create stronger collision, overflow, and clipping detectors
  - [x] first heuristic layer of overflow and imbalance risk exposed in review/QA
  - [x] summaries of the riskiest slides and clipping/overflow signals in QA reports
  - [x] first artifact analysis on the preview itself (edge contact / edge density)
  - [x] new layer of signals based on the useful preview body (safe-area intrusion, footer-boundary crowding, unsafe-corner density)
  - [x] first layer of layout-pressure/collision signals approximating real composition regions by slide type
  - [x] evolve toward detectors closer to real collision/clipping based on final preview/layout

Expected historical outcome: the project became ready to function as an **infrastructure block** inside other systems.

---

## Phase 5 — Optional intelligent layer

Historical objective: add intelligence without coupling the core to the LLM.

#### Preserved important direction

The core of the project should continue to be:

> structured content -> consistent rendering -> `.pptx`

Any AI layer should remain optional.

#### Preserved possibilities and progress

- [x] generate initial JSON from a structured briefing
- [x] expand an outline into structured slides
- [x] suggest initial titles, bullets, and KPIs from the briefing
- [x] summarize long text into executive content
- [x] suggest images or automatic placeholders
- [x] review content density per slide
- [x] use an LLM for iterative narrative review after the first deck is generated
- [x] use an LLM to rewrite titles, subtitles, and summaries in a more executive tone
- [x] use an LLM for slide-by-slide critique combining the briefing + visual QA
  - [x] first heuristic slide-by-slide critique derived from review/QA in AI-layer reports
  - [x] evolve toward LLM-driven critique combining the briefing + visual QA

#### Preserved providers and integrations

- [x] local GGUF provider via `llama.cpp` to experiment with `PPTAgent`
- [x] local provider via `Ollama`
- [x] initial remote providers via `OpenAI` and `Anthropic`
- [x] harden local execution in non-interactive mode with timeout and optional raw-output capture
- [x] adapt alternative local PPTAgent payloads to the canonical `ppt_creator` schema
- future evolution preserved: additional providers and deeper hardening of each integration

#### AI roadmap still open in the historical record

- [x] outline and narrative generation from a free-form briefing
- [x] executive rewriting of weak content
- [x] iterative deck review after rendering and QA
- [x] maintain a stronger loop: briefing -> structure -> render -> QA -> optional review -> new iteration
  - [x] first practical integration of generate + review + render inside the optional briefing CLI
  - [x] first automatic heuristic refine/re-review iteration in the optional CLI
  - [x] initial visual preview integration in the optional briefing pipeline
  - [x] initial preview integration derived from rendered `.pptx` in the optional briefing pipeline
  - [x] first automatic regeneration based on heuristic review feedback
  - [x] first incorporation of feedback also coming from visual preview into the optional heuristic loop
  - [x] evolve toward a stronger optional automatic iterative review/regeneration loop

Expected historical outcome: the project gained the potential to become a **deck-creation copilot** without compromising core simplicity.

---

### A.5. Preserved recommended execution order

#### High priority

1. **Phase 0 — MVP hardening**
2. **Phase 1 — A real design system**
3. **Phase 2 — Productization and DX**

#### Medium priority

4. **Phase 3 — Useful functional expansion**
5. **Phase 4 — Pipeline robustness**

#### Future priority

6. **Phase 5 — Optional intelligent layer**

---

### A.6. Preserved top 10 highest-impact improvements

1. refine the visual design and grid of the current slides
2. create more tests per layout
3. improve input JSON documentation
4. add CI
5. add lint/format
6. create 2 or 3 additional deck examples
7. support simple branding by theme/config
8. add essential new executive layouts
9. improve image fallback
10. create a release/versioning flow

---

### A.7. Preserved signals that the project became “very professional”

- new decks are created without changing source code
- the visuals remain consistent across different presentations
- the schema prevents most common errors
- the project runs locally and via Docker with low friction
- the tests cover the core reliably
- the documentation enables reuse in another project without additional verbal explanation
- new themes and layouts can be added without refactoring the core

---

### A.8. Preserved strategic backlog

- [x] export preview PNG per slide
- [x] generate automatic deck thumbnails
- [x] support simple charts generated from data
- [x] support executive tables with consistent style
- [x] reusable visual components library
- [x] internal marketplace for themes/layouts
- [x] integration with proposal/commercial workflow
- [x] API/service mode
- [x] future visual editor to assemble JSON with less friction

#### Preserved exhaustive maximum-impact improvement plan

##### Priority 1 — Preview fidelity and visual QA

- [x] preview generated from the real `.pptx`/PDF
- [x] stronger thumbnail sheet for visual inspection
- [x] debug overlays to analyze composition
- [x] initial heuristic quality review
- [x] automatic visual comparison between versions

##### Priority 2 — Layout-engine refactor

- [x] layout primitives (`stack`, `grid`, `two-column`, `panel row`)
  - [x] first utility base for inner bounds and vertical distribution of regions
  - [x] first application to already existing composed layouts
  - [x] first reusable horizontal distribution applied to executive rows/columns
  - [x] first simple grid composition applied to multi-panel layouts
  - [x] first higher-level semantic helpers reused in real layouts
  - [x] consolidate higher-level reusable primitives
  - [x] first practical consolidation with constrained columns/rows in covers, sections, charts, and timelines
  - [x] first expansion with additional semantic helpers for weighted panel-grid and reusable panel-content stacks
  - [x] new practical expansion with constrained panel grids/rows in additional composed layouts
  - [x] new practical consolidation with named helpers and reusable structured panels in multiple layouts
- [x] semantic constraints instead of excessively rigid positions
- [x] real text auto-fit per box
  - [x] first layer applied to critical homogeneous boxes
  - [x] initial expansion to executive layouts with greater density/overflow risk
  - [x] expansion to composed boxes, grids, and complex panels
- [x] automatic height and column balancing
  - [x] first content-weight-guided layer in key executive layouts
  - future evolution preserved: expand to even stronger, more consistent rules across the system
- [x] stronger visual overflow prevention

##### Priority 3 — Visual polish by layout

- [x] detailed review of `title`
- [x] detailed review of `metrics`
- [x] detailed review of `comparison` and `two_column`
- [x] detailed review of `table`
- [x] detailed review of `faq`
- [x] detailed review of `summary` and `closing`

##### Priority 4 — Image pipeline and placeholders

- [x] smarter crop
  - [x] first layer of cover-fit/crop applied to fixed image boxes (`image_text` + corresponding preview)
  - [x] first explicit focal-point layer (`image_focal_x` / `image_focal_y`) in render and preview for image-based slides
  - [x] first expansion of the strategy beyond `image_text`, applied to `title.hero_cover`
  - [x] new contextual expansion to `section`, including focal point in the corresponding synthetic preview
  - [x] expand the strategy to more layouts and focal-point/context rules
- [x] more premium and contextual placeholders
  - [x] first visual evolution of the structured placeholder in `image_text`
- [x] image suggestions by slide type, not just by general briefing
  - [x] first layer of more granular suggestions by slide/type in heuristic briefing analysis
  - [x] evolve to more contextual suggestions with focal point / asset style
- [x] basic asset and visual-style library

##### Priority 5 — Optional LLM for content and review

- [x] provider layer for multiple LLMs
- [x] local GGUF provider via `llama.cpp` to experiment with `PPTAgent`
- [x] outline and narrative generation from free briefing
- [x] executive rewriting of weak content
- [x] iterative deck review after rendering and QA

##### Priority 6 — Product / usage experience

- [x] lightweight visual editor
- [x] local playground to generate/edit/re-render decks
- [x] more robust local playground with template/profile bootstrap and basic operational controls
- [x] audience profiles (board, consulting, sales, product)
- [x] integration with commercial and operational workflows
  - [x] first library of operational/commercial workflow presets with bootstrap via CLI/API
  - [x] local playground can now load workflows and expose artifacts/previews in a more operational way

---

### A.9. Preserved practical next-cycle suggestion

Suggested sprint in the previous roadmap:

1. harden schema and CLI
2. visually refine the current layouts
3. add CI + lint/format
4. create 2 new examples
5. add 2 very useful new slide types

---

### A.10. Preserved executive summary

- **first**: consolidate what already exists
- **then**: raise visual and structural quality
- **next**: turn it into an easy tool to use and maintain
- **only after that**: expand themes, layouts, and optional intelligence

Preserved strategic message:

> strengthen the core, formalize the design system, productize usage, and only then expand.
