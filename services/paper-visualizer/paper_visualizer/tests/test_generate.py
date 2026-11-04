import json
from unittest.mock import patch

from paper_visualizer.backend import generate, ingest


def _setup_fake_content(tmp_path, monkeypatch):
    content = tmp_path / "content"
    content.mkdir()
    slug_dir = content / "slugA"
    slug_dir.mkdir()
    tex_file = tmp_path / "main.tex"
    tex_file.write_text("% fake\n", encoding="utf-8")
    meta = {
        "slug": "slugA",
        "source": {
            "tex_path": "main.tex",
            "pdf_path": None,
            "source_hash": "sha256:x",
            "ingested_at": "2026-04-16T00:00:00Z",
        },
        "title": {"en": "Paper A", "zh": ""},
        "short_title": {"en": "A", "zh": ""},
        "author": "Me",
        "date": "2026",
        "status": "draft",
        "abstract": {"tex": "abstract", "en": "", "zh": ""},
        "domain": [],
        "math_tools": [],
        "prerequisites": [],
        "main_theorems": [
            {
                "id": "thm:1",
                "env": "theorem",
                "statement_tex": "x=x",
                "section_number": "1",
                "label": {"en": "", "zh": ""},
                "key_ideas": {"en": [], "zh": []},
            }
        ],
        "sections": [{"number": "1", "title_tex": "Intro"}],
        "related_papers": [],
        "figures": [],
        "generation": None,
    }
    (slug_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr(generate, "CONTENT_DIR", content)
    monkeypatch.setattr(generate, "ROOT", tmp_path)
    monkeypatch.setattr(ingest, "CONTENT_DIR", content)
    monkeypatch.setattr(ingest, "ROOT", tmp_path)
    return content


def test_generate_one_mocked(tmp_path, monkeypatch):
    content = _setup_fake_content(tmp_path, monkeypatch)

    teach_output = "---\npaper_slug: slugA\nlang: en\n---\n## Context\nHi"
    classify_output = json.dumps(
        {
            "short_title": {"zh": "甲", "en": "Paper A"},
            "title_zh": "甲论文",
            "abstract": {"zh": "中文摘要", "en": "English abstract"},
            "domain": ["derivatives"],
            "math_tools": ["malliavin_calculus"],
            "prerequisites": [{"topic_id": "measure", "level": "basic", "why": "x"}],
            "related_papers": [],
            "main_theorems_labels": [
                {
                    "id": "thm:1",
                    "label_zh": "主定理",
                    "label_en": "Main",
                    "key_ideas_zh": ["a"],
                    "key_ideas_en": ["a"],
                }
            ],
        }
    )

    def fake_chat(model, messages, **kw):
        if "Classify" in messages[1]["content"] or "classif" in messages[1]["content"].lower():
            return classify_output
        return teach_output

    with patch.object(generate.vector_client, "chat", side_effect=fake_chat):
        result = generate.generate_one("slugA", force=False, langs=["en"])

    assert "generated" in result
    meta = json.loads((content / "slugA" / "meta.json").read_text(encoding="utf-8"))
    assert meta["domain"] == ["derivatives"]
    assert meta["main_theorems"][0]["label"]["zh"] == "主定理"
    assert meta["title"]["zh"] == "甲论文"
    assert meta["generation"]["prompt_version"] == generate.prompts.PROMPT_VERSION
    assert (content / "slugA" / "en.md").exists()

    with patch.object(generate.vector_client, "chat", side_effect=fake_chat):
        result2 = generate.generate_one("slugA", force=False, langs=["en"])
    assert "cached" in result2
