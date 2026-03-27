# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog, and the project aims to follow Semantic Versioning.

## [Unreleased]

### Added
- non-interactive llama.cpp execution hardening for the local `pptagent_local` provider, with timeout and optional raw-output capture
- normalization of PPTAgent-style local payloads into the project's canonical presentation schema so locally generated JSON can be validated and rendered even when the model returns an alternate slide structure
- horizontal layout primitives for reusable row/column distribution, now applied to metrics, cards, and table layouts
- simple grid composition helpers built on top of layout primitives, now applied to comparison, two-column, FAQ, and summary layouts
- higher-level semantic layout helpers for columns, panel rows, and panel grids, now reused across multiple executive layouts
- initial content-aware balancing for widths/heights in metrics, cards, table, comparison, two-column, FAQ, and summary layouts
- content-aware vertical stack balancing for mixed narrative regions such as comparison, two-column, and image-text slides
- optional office-aware preview backend selection with automatic fallback to synthetic previews
- initial layout primitive helpers for panel inner bounds and stacked vertical regions
- initial application of layout primitives to comparison, faq, cards, and two-column slides
- initial typographic auto-fit for critical homogeneous text boxes in rendered slides
- expanded initial auto-fit coverage to agenda, metrics, faq, table, and image-text layouts
- dedicated heuristic `review` flow in CLI/API for deck QA
- local GGUF/`llama.cpp` provider (`pptagent_local`) for the optional briefing layer
- provider interface for the optional briefing layer, with initial `heuristic` provider
- improved thumbnail contact sheets, preview debug overlays, and initial heuristic preview QA
- optional `ppt_creator_ai` layer to generate deck JSON from structured briefing input
- heuristic briefing analysis with executive summaries, image suggestions, and density review
- PNG slide preview generation plus thumbnail contact sheets
- `chart` slide type for simple data-driven charts
- lightweight HTTP API/service mode with health, template, validate, and render endpoints
- domain starter templates for `sales`, `consulting`, `strategy`, and `product`
- CLI `template` command to generate starter JSON decks by domain
- clearer CLI informational logs for validate/render/render-batch flows
- title `hero_cover` variant for alternate executive cover styling
- `two_column` slide type for side-by-side narrative framing
- `table` slide type for executive data summaries
- `faq` slide type for executive objections and appendix-style answers
- `agenda` slide type for discussion flow and meeting framing
- `summary` slide type for executive recap and closing synthesis
- `timeline` slide type for executive sequence storytelling
- `comparison` slide type for side-by-side decision framing
- branding metadata support (`client_name`, `footer_text`, `logo_path`)
- multiple built-in themes (`consulting_clean`, `dark_boardroom`, `startup_minimal`)
- CLI overrides for primary and secondary theme colors
- CLI dry-run mode with optional JSON reports
- batch rendering command for whole directories of input JSON files
- asset warning/report support for missing referenced images
- Phase 2 productization assets:
  - `Makefile`
  - `CHANGELOG.md`
  - GitHub Actions CI workflow
  - Ruff configuration
- Additional example decks for product strategy and board review scenarios
- Example validation/render coverage tests

## [0.1.0] - 2026-03-23

### Added
- Initial reusable `ppt_creator` module
- Executive Premium Minimal theme
- JSON schema validation with `pydantic`
- CLI for validation and rendering
- Dockerfile and helper scripts
- Roadmap and phased delivery plan
- Phase 0 hardening work
- Phase 1 design system foundations
