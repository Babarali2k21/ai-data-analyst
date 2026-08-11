.PHONY: install lint format typecheck test ingest profile ask ask-agent eval api web streamlit docker-up docker-demo

install:
	uv sync --group dev

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

eval:
	uv run eval-olist --mode $(or $(MODE),agent) $(ARGS)

api:
	uv run serve-api

web:
	cd apps/web && npm run dev -- --port 3001

streamlit:
	uv sync --group dev --group demo
	uv run streamlit run apps/streamlit/app.py --server.port 8501

docker-up:
	docker compose up --build

docker-demo:
	docker compose --profile demo up --build streamlit
