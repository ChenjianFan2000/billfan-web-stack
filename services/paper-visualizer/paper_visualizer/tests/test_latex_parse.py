from pathlib import Path

from paper_visualizer.backend import latex_parse

FIXTURES = Path(__file__).parent / "fixtures"


def test_minimal_paper():
    src = (FIXTURES / "minimal.tex").read_text(encoding="utf-8")
    parsed = latex_parse.parse_latex(src)
    assert parsed.title_tex == "A Minimal Test Paper"
    assert parsed.author_tex == "Test Author"
    assert parsed.date_tex == "2026"
    assert "test abstract" in parsed.abstract_tex
    assert len(parsed.sections) == 1
    assert parsed.sections[0].title_tex == "Introduction"
    assert parsed.sections[0].number == "1"
    assert parsed.theorems == []


def test_with_theorems():
    src = (FIXTURES / "with_theorems.tex").read_text(encoding="utf-8")
    parsed = latex_parse.parse_latex(src)
    assert parsed.title_tex == "Paper With Theorems"
    assert len(parsed.sections) == 2
    assert parsed.sections[0].number == "1"
    assert parsed.sections[1].number == "2"
    assert len(parsed.theorems) == 1
    thm = parsed.theorems[0]
    assert thm.id == "thm:main"
    assert thm.env == "theorem"
    assert "n^2" in thm.statement_tex
    assert thm.section_number == "1"
    assert "fig1.pdf" in parsed.figures


def test_source_hash_stable():
    h1 = latex_parse.source_hash("abc")
    h2 = latex_parse.source_hash("abc")
    assert h1 == h2
    assert h1.startswith("sha256:")
