"""Thin wrapper around the OpenAI SDK pointed at VectorEngine.

Reads VECTORENGINE_API_BASE / VECTORENGINE_API_KEY from the environment.
Exposes synchronous chat() and streaming chat_stream() helpers used by
generate.py and api.py.
"""
from __future__ import annotations

import os
import time
from typing import Iterator

import openai
from openai import OpenAI


def _client() -> OpenAI:
    base = os.environ.get("VECTORENGINE_API_BASE", "https://api.vectorengine.ai/v1")
    key = os.environ.get("VECTORENGINE_API_KEY")
    if not key:
        raise RuntimeError(
            "VECTORENGINE_API_KEY is not set. Copy paper_visualizer/.env.example "
            "to paper_visualizer/.env and fill in your key."
        )
    return OpenAI(base_url=base, api_key=key, timeout=600.0, max_retries=0)


def chat(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.3,
    max_tokens: int = 20000,
    retries: int = 3,
) -> str:
    """Synchronous chat completion with retry on transient errors.

    Internally uses streaming and concatenates tokens because the upstream
    gateway drops large non-streaming responses with SSL record-MAC errors.
    """
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            stream = _client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            parts: list[str] = []
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    parts.append(delta)
            return "".join(parts)
        except (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
        ) as e:
            last_exc = e
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise
    raise RuntimeError(f"chat() exhausted retries: {last_exc}")


def chat_stream(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> Iterator[str]:
    """Yield content deltas as they arrive from the streaming endpoint."""
    stream = _client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
