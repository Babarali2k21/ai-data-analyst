# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY datasets ./datasets
COPY tests/fixtures/olist ./tests/fixtures/olist
COPY data/demo ./data/demo
COPY apps/streamlit ./apps/streamlit
COPY .streamlit ./.streamlit

RUN uv sync --frozen --no-dev --no-editable \
    && uv pip install "streamlit>=1.42.0"

ENV PATH="/app/.venv/bin:$PATH" \
    DUCKDB_PATH=/app/data/demo/analytics.duckdb \
    DEMO_DUCKDB_PATH=/app/data/demo/analytics.duckdb \
    OLIST_METADATA_DIR=/app/datasets/olist \
    CHARTS_DIR=/app/data/runtime/charts \
    DEMO_QUOTA_PATH=/app/data/runtime/quota.sqlite \
    DEMO_QUERY_LIMIT=3 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

RUN mkdir -p /app/data/runtime/charts

EXPOSE 8000 8501
CMD ["serve-api"]
