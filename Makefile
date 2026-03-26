PYTHON ?= /Users/danyellambert/hf_llm_playground/.conda-env/bin/python
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest
RUFF := $(PYTHON) -m ruff
QUALITY_PATHS := ppt_creator tests

.PHONY: install install-dev test lint format validate-example render-example render-all-examples docker-render-example ci

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

render-all-examples:
	$(PYTHON) -m ppt_creator.cli render examples/ai_sales.json outputs/ai_sales_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/product_strategy.json outputs/product_strategy_makefile.pptx
	$(PYTHON) -m ppt_creator.cli render examples/board_review.json outputs/board_review_makefile.pptx

docker-render-example:
	docker build -t ppt-creator .
	docker run --rm -v "$$PWD:/work" ppt-creator python -m ppt_creator.cli render /work/examples/ai_sales.json /work/outputs/ai_sales_docker_makefile.pptx

ci:
	$(RUFF) check $(QUALITY_PATHS)
	$(PYTEST) -q
