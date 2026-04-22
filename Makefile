PYTHON ?= $(CURDIR)/.conda-env/bin/python
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
QUALITY_PATHS := ppt_creator ppt_creator_ai tests

.PHONY: install install-dev test lint format validate-example render-example render-all-examples review-example review-pptx-example playground api generate-briefing-example docker-render-example docker-api-build docker-api docker-api-down docker-api-cloud docker-api-cloud-down gallery layout-audit ai-benchmark build-dist check-dist release-smoke ci

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

test:
	$(PYTEST) -q

lint:
	$(RUFF) check $(QUALITY_PATHS)

format:
	$(RUFF) format $(QUALITY_PATHS)

validate-example:
	$(PYTHON) -m ppt_creator.cli validate examples/ai_sales.json

render-example:
	$(PYTHON) -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales_makefile.pptx

review-example:
	$(PYTHON) -m ppt_creator.cli review examples/ai_sales.json --preview-dir outputs/ai_sales_review_makefile --report-json outputs/ai_sales_review_makefile.json

review-pptx-example:
	$(PYTHON) -m ppt_creator.cli review-pptx outputs/ai_sales.pptx outputs/ai_sales_review_pptx_makefile --report-json outputs/ai_sales_review_pptx_makefile.json

playground:
	$(PYTHON) -m ppt_creator.api --host 127.0.0.1 --port 8787 --asset-root examples

api: playground

render-all-examples:
	$(PYTHON) -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/product_strategy.json outputs/product_strategy_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/board_review.json outputs/board_review_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/sales_qbr.json outputs/sales_qbr_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/board_strategy_review.json outputs/board_strategy_review_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/product_operating_review.json outputs/product_operating_review_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/consulting_steerco.json outputs/consulting_steerco_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/layout_showcase.json outputs/layout_showcase_makefile.pptx

generate-briefing-example:
	$(PYTHON) -m ppt_creator_ai.cli generate examples/briefing_sales.json outputs/briefing_sales_makefile.json --analysis-json outputs/briefing_sales_makefile_analysis.json

gallery:
	$(PYTHON) bin/generate_gallery.py

layout-audit:
	$(PYTHON) bin/audit_layout_showcase.py

ai-benchmark:
	$(PYTHON) -m ppt_creator_ai.cli benchmark outputs/ai_benchmark --provider heuristic --write-json-decks --report-json outputs/ai_benchmark/report.json

docker-render-example:
	docker build -t ppt-creator .
	docker run --rm -v "$$PWD:/work" ppt-creator python -m ppt_creator.cli render /work/examples/ai_sales.json /work/outputs/ai_sales_docker_makefile.pptx

docker-api-build:
	docker compose build ppt_creator_api

docker-api:
	docker compose up --build ppt_creator_api

docker-api-down:
	docker compose down

docker-api-cloud:
	docker compose --profile cloudlike up --build ppt_creator_api_cloud

docker-api-cloud-down:
	docker compose --profile cloudlike down

build-dist:
	rm -rf dist build *.egg-info
	$(PYTHON) -m build

check-dist: build-dist
	$(PYTHON) -m twine check dist/*

release-smoke: check-dist
	$(PIP) install --force-reinstall dist/*.whl
	ppt-creator --help >/dev/null
	ppt-creator-ai --help >/dev/null

ci:
	$(RUFF) check $(QUALITY_PATHS)
	$(PYTEST) -q
