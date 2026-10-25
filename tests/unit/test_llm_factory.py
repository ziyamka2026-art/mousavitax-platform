"""
Unit tests for the LLM provider factory.
"""

import os

import pytest

from app.llm.factory import (
    ChatMessage,
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    OpenAIProvider,
    get_llm,
)


@pytest.mark.unit
def test_chat_message_dataclass():
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


@pytest.mark.unit
def test_get_llm_ollama_in_dev(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("NODE_ENV", "development")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OPENAI_MODEL", "qwen2.5:7b")

    # Reset the singleton
    import app.llm.factory as mod
    mod._provider = None

    provider = get_llm()
    assert isinstance(provider, OllamaProvider)
    assert provider.name == "ollama"


@pytest.mark.unit
def test_get_llm_refuses_ollama_in_production(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("VERCEL_ENV", "production")

    import app.llm.factory as mod
    mod._provider = None

    with pytest.raises(RuntimeError, match="not supported in production"):
        get_llm()


@pytest.mark.unit
def test_get_llm_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("NODE_ENV", "development")

    import app.llm.factory as mod
    mod._provider = None

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        get_llm()


@pytest.mark.unit
def test_get_llm_gemini_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("NODE_ENV", "development")

    import app.llm.factory as mod
    mod._provider = None

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        get_llm()


@pytest.mark.unit
def test_get_llm_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("NODE_ENV", "development")

    import app.llm.factory as mod
    mod._provider = None

    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_llm()


@pytest.mark.unit
def test_openai_provider_has_correct_name_and_model():
    p = OpenAIProvider(
        api_key="sk-test",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
    )
    assert p.name == "openai"
    assert p.model == "gpt-4o-mini"


@pytest.mark.unit
def test_gemini_provider_has_correct_name_and_model():
    p = GeminiProvider(api_key="AIzaTest", model="gemini-2.0-flash-lite")
    assert p.name == "gemini"
    assert p.model == "gemini-2.0-flash-lite"
