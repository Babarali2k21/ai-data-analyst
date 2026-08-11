.PHONY: install lint format typecheck test ingest profile ask ask-agent eval api web streamlit docker-up docker-demo aws-bootstrap aws-push-image aws-app-runner

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

aws-bootstrap:
	chmod +x scripts/aws-bootstrap.sh
	./scripts/aws-bootstrap.sh

aws-push-image:
	chmod +x scripts/aws-push-image.sh
	./scripts/aws-push-image.sh $(TAG)

aws-app-runner:
	cd infra/aws && terraform apply -var='create_app_runner=true' -auto-approve
	@echo "Service URL:" && cd infra/aws && terraform output -raw app_runner_service_url
	@echo "Set GitHub variable APP_RUNNER_SERVICE_ARN to:" && cd infra/aws && terraform output -raw app_runner_service_arn
