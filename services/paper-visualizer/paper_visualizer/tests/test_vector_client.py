from unittest.mock import patch, MagicMock

import pytest

from paper_visualizer.backend import vector_client


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("VECTORENGINE_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="VECTORENGINE_API_KEY"):
        vector_client._client()


def test_chat_returns_content(monkeypatch):
    monkeypatch.setenv("VECTORENGINE_API_KEY", "sk-fake")
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="hel"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="lo"))]),
    ]
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = iter(chunks)
    with patch.object(vector_client, "_client", return_value=fake_client):
        out = vector_client.chat("gpt-x", [{"role": "user", "content": "hi"}])
    assert out == "hello"


def test_chat_stream_yields_tokens(monkeypatch):
    monkeypatch.setenv("VECTORENGINE_API_KEY", "sk-fake")
    chunks = [
        MagicMock(choices=[MagicMock(delta=MagicMock(content="he"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content="llo"))]),
        MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
    ]
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = iter(chunks)
    with patch.object(vector_client, "_client", return_value=fake_client):
        tokens = list(vector_client.chat_stream("gpt-x", []))
    assert tokens == ["he", "llo"]
