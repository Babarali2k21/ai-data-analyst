"""LangChain callback that records LLM latency and token usage."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from ai_data_analyst.observability.context import get_run_metrics


class MetricsCallbackHandler(BaseCallbackHandler):
    """Attach via ChatOpenAI(callbacks=[...]) to populate RunMetrics."""

    def __init__(self) -> None:
        super().__init__()
        self._starts: dict[UUID, float] = {}

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._starts[run_id] = time.perf_counter()

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._starts[run_id] = time.perf_counter()

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        started = self._starts.pop(run_id, None)
        latency_ms = (time.perf_counter() - started) * 1000 if started else 0.0
        prompt_tokens = 0
        completion_tokens = 0

        usage = (response.llm_output or {}).get("token_usage") or {}
        if usage:
            prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            completion_tokens = int(
                usage.get("completion_tokens") or usage.get("output_tokens") or 0
            )
        else:
            for generation_list in response.generations:
                for generation in generation_list:
                    message = getattr(generation, "message", None)
                    meta = getattr(message, "usage_metadata", None) if message else None
                    if isinstance(meta, dict):
                        prompt_tokens += int(meta.get("input_tokens") or 0)
                        completion_tokens += int(meta.get("output_tokens") or 0)
                        continue
                    resp_meta = getattr(message, "response_metadata", None) if message else None
                    if isinstance(resp_meta, dict):
                        token_usage = resp_meta.get("token_usage") or resp_meta.get("usage") or {}
                        prompt_tokens += int(
                            token_usage.get("prompt_tokens")
                            or token_usage.get("input_tokens")
                            or 0
                        )
                        completion_tokens += int(
                            token_usage.get("completion_tokens")
                            or token_usage.get("output_tokens")
                            or 0
                        )

        metrics = get_run_metrics()
        if metrics is not None:
            metrics.mark_llm(
                latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        started = self._starts.pop(run_id, None)
        latency_ms = (time.perf_counter() - started) * 1000 if started else 0.0
        metrics = get_run_metrics()
        if metrics is not None:
            metrics.mark_llm(latency_ms)
            metrics.tool_errors += 1
