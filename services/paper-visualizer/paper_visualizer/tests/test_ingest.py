import json

from paper_visualizer.backend import ingest


def test_ingest_one(tmp_path, monkeypatch):
    output = tmp_path / "output"
    (output / "paperA").mkdir(parents=True)
    tex = output / "paperA" / "main.tex"
    tex.write_text(
        r"""
\documentclass{article}
\title{Paper A}
\author{Me}
\begin{document}
\maketitle
\begin{abstract}Abs.\end{abstract}
\section{S1}
\end{document}
""",
        encoding="utf-8",
    )
    content_dir = tmp_path / "content"
    monkeypatch.setattr(ingest, "ROOT", tmp_path)
    monkeypatch.setattr(ingest, "OUTPUT_DIR", output)
    monkeypatch.setattr(ingest, "CONTENT_DIR", content_dir)

    result = ingest.ingest_one("paperA", output / "paperA")
    assert "ingested paperA" in result

    meta = json.loads((content_dir / "paperA" / "meta.json").read_text(encoding="utf-8"))
    assert meta["slug"] == "paperA"
    assert meta["title"]["en"] == "Paper A"
    assert meta["author"] == "Me"
    assert len(meta["sections"]) == 1

    result2 = ingest.ingest_one("paperA", output / "paperA")
    assert "cached" in result2

    result3 = ingest.ingest_one("paperA", output / "paperA", force=True)
    assert "ingested" in result3
