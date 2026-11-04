import json

import pytest
from fastapi.testclient import TestClient

from paper_visualizer.backend import api as api_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    content = tmp_path / "content"
    (content / "slugA").mkdir(parents=True)
    (content / "papers.json").write_text(
        json.dumps(
            {
                "generated_at": "now",
                "papers": [
                    {
                        "slug": "slugA",
                        "short_title": {"zh": "甲", "en": "Paper A"},
                        "status": "draft",
                        "domain": ["derivatives"],
                        "math_tools": ["x"],
                        "one_liner": "Hi",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (content / "tags.json").write_text(
        json.dumps({"domains": {}, "math_tools": {}}), encoding="utf-8"
    )
    (content / "slugA" / "meta.json").write_text(
        json.dumps(
            {
                "slug": "slugA",
                "title": {"en": "Paper A", "zh": "甲"},
                "short_title": {"zh": "甲", "en": "Paper A"},
                "source": {"tex_path": "fake.tex"},
                "abstract": {"tex": "abs", "zh": "", "en": ""},
                "main_theorems": [],
                "author": "Me",
                "date": "2026",
                "status": "draft",
                "domain": [],
                "math_tools": [],
                "prerequisites": [],
                "sections": [],
                "related_papers": [],
                "figures": [],
                "generation": None,
            }
        ),
        encoding="utf-8",
    )
    (content / "slugA" / "en.md").write_text("## Context\nHi", encoding="utf-8")
    (content / "slugA" / "zh.md").write_text("## 背景\n你好", encoding="utf-8")

    (tmp_path / "fake.tex").write_text("% fake", encoding="utf-8")

    monkeypatch.setattr(api_mod, "CONTENT_DIR", content)
    monkeypatch.setattr(api_mod, "ROOT", tmp_path)
    monkeypatch.setattr(api_mod, "FRONTEND_DIST", tmp_path / "nonexistent")

    return TestClient(api_mod.create_app())


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["papers_count"] == 1


def test_list_papers(client):
    r = client.get("/api/papers")
    assert r.status_code == 200
    assert r.json()["papers"][0]["slug"] == "slugA"


def test_detail(client):
    r = client.get("/api/papers/slugA")
    assert r.status_code == 200
    data = r.json()
    assert data["meta"]["slug"] == "slugA"
    assert "Context" in data["content"]["en"]
    assert "背景" in data["content"]["zh"]


def test_detail_404(client):
    r = client.get("/api/papers/ghost")
    assert r.status_code == 404


def test_chat_streams(client, monkeypatch):
    def fake_stream(model, messages, **kw):
        yield "hello"
        yield " world"

    monkeypatch.setattr(api_mod.vector_client, "chat_stream", fake_stream)

    r = client.post(
        "/api/chat",
        json={
            "paper_slug": "slugA",
            "message": "why?",
            "history": [],
            "lang": "en",
        },
    )
    assert r.status_code == 200
    body = r.text
    assert "event: token" in body
    assert "hello" in body
    assert "event: done" in body
