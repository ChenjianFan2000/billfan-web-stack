import importlib

import pytest
from fastapi import HTTPException

from app import aimath


def _consume_stream(chunks) -> str:
    parts = []
    for chunk in chunks:
        if isinstance(chunk, bytes):
            parts.append(chunk.decode("utf-8"))
        else:
            parts.append(str(chunk))
    return "".join(parts)


def test_rewrite_aimath_api_path():
    main = importlib.import_module("app.main")

    assert main._rewrite_aimath_api_path("/api/health") == "/api/aimath/health"
    assert main._rewrite_aimath_api_path("/api/papers") == "/api/aimath/papers"
    assert main._rewrite_aimath_api_path("/api/papers/cross_impact") == "/api/aimath/papers/cross_impact"
    assert main._rewrite_aimath_api_path("/api/tags") == "/api/aimath/tags"
    assert main._rewrite_aimath_api_path("/api/chat") == "/api/aimath/chat"
    assert main._rewrite_aimath_api_path("/api/unknown") == ""


def test_cors_origins_always_include_aimath(monkeypatch):
    main = importlib.import_module("app.main")
    monkeypatch.setenv("CORS_ORIGINS", "https://billfan.cn,https://www.billfan.cn")

    origins = main._cors_origins()

    assert "https://billfan.cn" in origins
    assert "https://www.billfan.cn" in origins
    assert "https://aimath.billfan.cn" in origins


def test_aimath_health_and_index():
    payload = aimath.aimath_health()
    index_payload = aimath.aimath_papers()

    assert payload["status"] == "ok"
    assert payload["papers_count"] >= 1
    assert len(index_payload["papers"]) == payload["papers_count"]


def test_aimath_tags_and_detail():
    tags = aimath.aimath_tags()
    detail = aimath.aimath_paper_detail("cross_impact")

    assert "domains" in tags
    assert "math_tools" in tags
    assert detail["meta"]["slug"] == "cross_impact"
    assert detail["content"]["zh"]
    assert detail["content"]["en"]


def test_aimath_detail_rejects_invalid_slug():
    with pytest.raises(HTTPException) as exc_info:
        aimath.aimath_paper_detail("../secrets")

    assert exc_info.value.status_code == 404


def test_aimath_chat_reports_missing_api_key(monkeypatch):
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)

    payload = aimath.AimathChatRequest(
        paper_slug="cross_impact",
        message="解释主定理",
        history=[],
        lang="zh",
    )
    response = aimath.aimath_chat(payload)
    body = _consume_stream(aimath._chat_event_stream(payload))

    assert response.headers["x-accel-buffering"] == "no"
    assert "event: error" in body
    assert "LLM API key is not configured" in body


def test_aimath_chat_streams_tokens(monkeypatch):
    captured = {}

    def fake_call_messages(**kwargs):
        captured.update(kwargs)
        return {
            "content": [
                {
                    "type": "text",
                    "text": "这是一个测试回答，用于验证 SSE token 和 done 事件。",
                }
            ]
        }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(aimath.dashscope_client, "call_messages", fake_call_messages)

    payload = aimath.AimathChatRequest(
        paper_slug="cross_impact",
        message="Explain theorem 1",
        history=[
            aimath.AimathChatMessage(role="assistant", content="Earlier answer"),
            aimath.AimathChatMessage(role="system", content="ignored"),
        ],
        lang="en",
        current_section="Main Results",
    )
    response = aimath.aimath_chat(payload)
    body = _consume_stream(aimath._chat_event_stream(payload))

    assert response.headers["cache-control"] == "no-cache"
    assert "event: token" in body
    assert "event: done" in body
    assert "这是一个测试回答" in body
    assert captured["messages"] == [
        {"role": "assistant", "content": "Earlier answer"},
        {"role": "user", "content": "Explain theorem 1"},
    ]
    assert captured["model"] == aimath._chat_model()
    assert "No-Manipulation Conditions for Heterogeneous Power-Law Cross-Impact Kernels" in captured["system_prompt"]
    assert "The student is currently reading section: Main Results" in captured["system_prompt"]


def test_aimath_chat_falls_back_to_secondary_model(monkeypatch):
    attempts = []

    def fake_call_messages(**kwargs):
        attempts.append(kwargs["model"])
        if kwargs["model"] == "GPT-5.5-high":
            return {}
        return {
            "content": [
                {
                    "type": "text",
                    "text": "fallback ok",
                }
            ]
        }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setenv("AIMATH_MODEL", "GPT-5.5-high")
    monkeypatch.setenv("QWEN_MODEL", "claude-opus-4-6")
    monkeypatch.setenv("AIMATH_FALLBACK_MODEL", "claude-opus-4-6")
    monkeypatch.setattr(aimath.dashscope_client, "call_messages", fake_call_messages)

    payload = aimath.AimathChatRequest(
        paper_slug="cross_impact",
        message="Explain theorem 1",
        history=[],
        lang="en",
    )
    body = _consume_stream(aimath._chat_event_stream(payload))

    assert attempts == ["GPT-5.5-high", "claude-opus-4-6"]
    assert "fallback ok" in body
