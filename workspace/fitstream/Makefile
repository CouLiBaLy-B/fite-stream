# FitStream Makefile
# Quick commands for development and usage

.PHONY: help setup test lint typecheck check format download-model animate story serve clean precommit-install precommit-run

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================
# Setup
# ============================================================

setup:  ## Full environment setup
	bash scripts/setup.sh

install:  ## Install FitStream in development mode
	pip install -e ".[dev]"

download-model:  ## Download default model (VACE 1.3B)
	python scripts/download_models.py --model vace-1.3b

download-14b:  ## Download VACE 14B model (needs 48GB+ VRAM)
	python scripts/download_models.py --model vace-14b

download-loom:  ## Download LoomVideo model
	python scripts/download_models.py --model loomvideo

list-models:  ## List available models
	python scripts/download_models.py --model list

# ============================================================
# Usage
# ============================================================

animate:  ## Generate animation (usage: make animate IMAGE=photo.jpg PROMPT="...")
	PYTHONPATH=. python -m fitstream.cli animate \
		--image $(IMAGE) \
		--prompt "$(PROMPT)" \
		--preset standard

story:  ## Generate story (usage: make story IMAGE=photo.jpg STORY="...")
	PYTHONPATH=. python -m fitstream.cli story \
		--image $(IMAGE) \
		--story "$(STORY)" \
		--preset standard

status:  ## Show system status
	PYTHONPATH=. python -m fitstream.cli status

# ============================================================
# API Server
# ============================================================

serve:  ## Start the API server
	PYTHONPATH=. python -m fitstream.api.server

serve-dev:  ## Start API with auto-reload
	PYTHONPATH=. uvicorn fitstream.api.server:app --host 0.0.0.0 --port 8000 --reload

streamlit:  ## Start the Streamlit frontend
	streamlit run streamlit/app.py

# ============================================================
# Development
# ============================================================

test:  ## Run all tests
	PYTHONPATH=. python -m pytest tests/ -v

test-fast:  ## Run fast tests only (no GPU needed)
	PYTHONPATH=. python -m pytest tests/ -v -k "not gpu"

lint:  ## Lint code
	ruff check fitstream/ tests/

format:  ## Format code
	ruff format fitstream/ tests/
	black fitstream/ tests/

typecheck:  ## Static type checking with mypy
	PYTHONPATH=. python -m mypy fitstream/ --no-error-summary

check: lint typecheck test-fast  ## Run all checks (lint + type + tests)

precommit-install:  ## Install pre-commit hooks
	pre-commit install

precommit-run:  ## Run pre-commit on all files
	pre-commit run --all-files

clean:  ## Clean generated files
	rm -rf outputs/* uploads/* __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# ============================================================
# Demo
# ============================================================

demo-story:  ## Run demo story generation
	@echo "📖 Running demo story..."
	PYTHONPATH=. python -c "\
from fitstream.core.utils.prompt_utils import split_story_to_scenes, create_story_summary; \
story = 'Marie walks through a sunny Parisian street. She stops at a flower shop and picks a rose. She sits at a café terrace watching the sunset.'; \
scenes = split_story_to_scenes(story, style='cinematic'); \
print(create_story_summary(scenes)); \
print(); \
for s in scenes: \
    print(f'  Scene {s.index+1}: [{s.duration_hint}] [{s.camera}] [{s.mood}]'); \
    print(f'    {s.prompt[:120]}'); \
    print(); \
"
