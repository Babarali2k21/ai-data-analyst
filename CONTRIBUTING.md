# Contributing

Thanks for your interest in contributing to **AI Data Analyst**, a product of [CodeLink Systems](https://codelink.systems).

## Development setup

```bash
uv sync --group dev
cp .env.example .env   # set OPENAI_API_KEY for live LLM calls
make ingest && make profile   # full Olist DB (optional for unit tests)

cd apps/web && npm install && cp .env.local.example .env.local
```

## Checks before opening a PR

```bash
make lint
make typecheck
make test
cd apps/web && npm run build
```

## Guidelines

1. Follow **DRY, KISS, YAGNI, SOLID, SoC, and SSOT**.
2. Keep HTTP adapters thin (`api/routes`); put orchestration in `api/services`.
3. Do not commit secrets (`.env`, API keys, local DuckDB dumps beyond `data/demo`).
4. Prefer small, focused PRs with a clear summary and test plan.
5. Be respectful — see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Architecture sketch

Dependencies flow downward only:

`api` → `agent` / `analyst` → `tools` → `data`

Cross-cutting: `security/`, `observability/`.

## License

By contributing, you agree that your contributions are licensed under the MIT License (see [LICENSE](LICENSE)).
