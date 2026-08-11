.PHONY: install lint format typecheck test ingest profile ask ask-agent

install:
	uv sync --all-groups

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run mypy src

test:
	uv run pytest

ingest:
	uv run ingest-olist

profile:
	uv run profile-olist

ask:
	uv run ask-sql $(Q)

ask-agent:
	uv run ask-agent $(Q)
