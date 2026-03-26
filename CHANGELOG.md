# Changelog

All notable changes to this project will be documented in this file.

The format is inspired by Keep a Changelog, and the project aims to follow Semantic Versioning.

## [Unreleased]

### Added
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
