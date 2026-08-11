"""LLM client helpers."""

from __future__ import annotations

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from ai_data_analyst.config import Settings, get_settings


def get_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Return a configured ChatOpenAI client from Settings."""
    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=SecretStr(settings.openai_api_key),
        temperature=settings.llm_temperature,
    )
