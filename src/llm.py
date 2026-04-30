"""
Swappable LLM client. Supports Groq (cloud, free tier) and Ollama (local).
Selection is driven by the LLM_PROVIDER env var.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base for any LLM provider."""

    @abstractmethod
    def complete_json(self, prompt: str) -> str:
        """Send a prompt and return the raw JSON string response."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the provider + model."""


class GroqClient(LLMClient):
    """
    Groq with Llama 3.3 70B (default).
    Free tier: ~30 requests/minute, ~14,400 requests/day. No credit card required.
    Get a key at https://console.groq.com
    """

    def __init__(self, model: str = "llama-3.3-70b-versatile") -> None:
        from groq import Groq

        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY not set. Get a free key at console.groq.com "
                "and put it in .env"
            )
        self._client = Groq(api_key=api_key)
        self._model = model

    def complete_json(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or ""

    @property
    def name(self) -> str:
        return f"Groq({self._model})"


class OllamaClient(LLMClient):
    """
    Ollama runs locally; fully free, fully offline.
    Install from https://ollama.com, then: `ollama pull llama3.1:8b`
    """

    def __init__(
        self,
        model: str = "llama3.1:8b",
        host: str = "http://localhost:11434",
    ) -> None:
        import ollama

        self._client = ollama.Client(host=host)
        self._model = model

    def complete_json(self, prompt: str) -> str:
        response = self._client.chat(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
            options={"temperature": 0.2},
        )
        return response["message"]["content"]

    @property
    def name(self) -> str:
        return f"Ollama({self._model})"


def get_llm() -> LLMClient:
    """Factory — reads LLM_PROVIDER env var, returns the right client."""
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
        return GroqClient(model=model)

    if provider == "ollama":
        model = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        return OllamaClient(model=model, host=host)

    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider!r}. Use 'groq' or 'ollama'."
    )