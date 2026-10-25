"""
LLM Provider Factory — MousaviTax AI Platform
================================================

Pluggable LLM abstraction supporting three providers:
  * ollama  — local Ollama server (development default)
  * openai  — OpenAI API (production recommended)
  * gemini  — Google Gemini API

Switch via LLM_PROVIDER env var. Production safety: refuses to start
with `ollama` in production — prevents accidental deployment of a
local-only stack to a serverless host.

@package apps.api.app.llm.factory
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: dict[str, int]  # {prompt_tokens, completion_tokens, total_tokens}
    raw: dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract LLM interface — implement per provider."""

    @abstractmethod
    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse: ...

    @abstractmethod
    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...


    @property
    @abstractmethod
    def name(self) -> str: ...


    @property
    @abstractmethod
    def model(self) -> str: ...


# ---------------------------------------------------------------------------
# Ollama — local development
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Ollama local server — for development only."""

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        **({"num_predict": max_tokens} if max_tokens else {}),
                    },
                },
            )
            res.raise_for_status()
            data = res.json()
            return ChatResponse(
                content=data["message"]["content"],
                model=self._model,
                usage={
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": (
                        data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
                    ),
                },
                raw=data,
            )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [{"role": m.role, "content": m.content} for m in messages],
                    "stream": True,
                    "options": {"temperature": temperature},
                },
            ) as res:
                res.raise_for_status()
                async for line in res.aiter_lines():
                    if not line.strip():
                        continue
                    import json
                    chunk = json.loads(line)
                    if chunk.get("message", {}).get("content"):
                        yield chunk["message"]["content"]

    async def embed(self, text: str) -> list[float]:
        # Delegate to embedding-service package in production — this is a
        # simple fallback for testing only.
        embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": embedding_model, "prompt": text},
            )
            res.raise_for_status()
            return res.json()["embedding"]


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAIProvider(LLMProvider):
    """OpenAI-compatible API (works with Azure OpenAI too via OPENAI_BASE_URL)."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            res.raise_for_status()
            data = res.json()
            return ChatResponse(
                content=data["choices"][0]["message"]["content"],
                model=data.get("model", self._model),
                usage={
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                },
                raw=data,
            )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=body,
            ) as res:
                res.raise_for_status()
                async for line in res.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        return
                    import json
                    chunk = json.loads(payload)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    if delta.get("content"):
                        yield delta["content"]

    async def embed(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(
                f"{self._base_url}/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": "text-embedding-3-small",
                    "input": text,
                },
            )
            res.raise_for_status()
            return res.json()["data"][0]["embedding"]


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------

class GeminiProvider(LLMProvider):
    """Google Gemini API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def model(self) -> str:
        return self._model

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        # Convert to Gemini format: contents[] with role mapping
        contents = []
        system_prompt = ""
        for m in messages:
            if m.role == "system":
                system_prompt += m.content + "\n"
                continue
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        body = {
            "contents": contents,
            "generationConfig": {"temperature": temperature},
        }
        if system_prompt:
            body["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if max_tokens:
            body["generationConfig"]["maxOutputTokens"] = max_tokens

        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(url, json=body)
            res.raise_for_status()
            data = res.json()
            content = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            usage_meta = data.get("usageMetadata", {})
            return ChatResponse(
                content=content,
                model=self._model,
                usage={
                    "prompt_tokens": usage_meta.get("promptTokenCount", 0),
                    "completion_tokens": usage_meta.get("candidatesTokenCount", 0),
                    "total_tokens": usage_meta.get("totalTokenCount", 0),
                },
                raw=data,
            )

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # Gemini streaming has a different API — implement if needed.
        # For now, fall back to non-streaming and yield once.
        res = await self.complete(
            messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
        yield res.content

    async def embed(self, text: str) -> list[float]:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"text-embedding-004:embedContent?key={self._api_key}"
        )
        body = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            res = await client.post(url, json=body)
            res.raise_for_status()
            data = res.json()
            return data["embedding"]["values"]


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_provider: LLMProvider | None = None


def get_llm() -> LLMProvider:
    """Return the configured LLM provider singleton."""
    global _provider
    if _provider:
        return _provider

    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    is_prod = (
        os.getenv("NODE_ENV") == "production"
        or os.getenv("VERCEL_ENV") == "production"
    )

    # Production safety — refuse to start with Ollama in prod
    if provider == "ollama" and is_prod:
        raise RuntimeError(
            "LLM_PROVIDER=ollama is not supported in production. "
            "Set LLM_PROVIDER=openai or LLM_PROVIDER=gemini."
        )

    if provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = os.getenv("OPENAI_MODEL", "qwen2.5:7b")
        _provider = OllamaProvider(base_url=base_url, model=model)
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_PROVIDER=openai requires OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        _provider = OpenAIProvider(api_key=api_key, base_url=base_url, model=model)
    elif provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("LLM_PROVIDER=gemini requires GOOGLE_API_KEY")
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        _provider = GeminiProvider(api_key=api_key, model=model)
    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r} (expected ollama|openai|gemini)"
        )

    return _provider


__all__ = [
    "LLMProvider",
    "ChatMessage",
    "ChatResponse",
    "OllamaProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "get_llm",
]
