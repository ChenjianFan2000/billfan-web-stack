"""Scan papers from multiple repos, parse LaTeX, extract quality metrics.

Supports two repo layouts:
  - Realresearch: output/{slug}/main_v2.tex (or main.tex)
  - structural_research: projects/{id}/output/main.tex

Usage:
    python -m paper_visualizer.backend.ingest
    python -m paper_visualizer.backend.ingest --slug project8 --force
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from paper_visualizer.backend import eval_extract, latex_parse

# Source-tex root for the primary (Realresearch) repo.
# Defaults to the parent of paper_visualizer/, which is the Realresearch
# checkout when running in-tree. Override with PAPER_VISUALIZER_SOURCE_ROOT
# when deploying standalone.
_DEFAULT_ROOT = Path(__file__).resolve().parents[2]
ROOT = Path(os.environ.get("PAPER_VISUALIZER_SOURCE_ROOT", _DEFAULT_ROOT))
CONTENT_DIR = Path(__file__).resolve().parent / "content"

# Optional second repo. If unset or path missing, structural_research scanning
# is skipped silently.
_STRUCTURAL_ENV = os.environ.get("PAPER_VISUALIZER_STRUCTURAL_ROOT")
STRUCTURAL_ROOT = Path(_STRUCTURAL_ENV) if _STRUCTURAL_ENV else None


class PaperSource(NamedTuple):
    slug: str
    tex_dir: Path  # directory containing main*.tex
    repo_root: Path
    repo_type: str  # "realresearch" or "structural"
    project_id: str | None  # e.g. "p006" for structural


def discover_papers() -> list[PaperSource]:
    """Discover papers from all configured repos."""
    papers: list[PaperSource] = []

    # Realresearch: output/{slug}/
    rr_output = ROOT / "output"
    if rr_output.exists():
        for d in sorted(rr_output.iterdir()):
            if d.is_dir() and find_tex_file(d):
                papers.append(PaperSource(d.name, d, ROOT, "realresearch", None))

    # structural_research: projects/{id}/output/
    if STRUCTURAL_ROOT is not None and STRUCTURAL_ROOT.exists():
        projects_dir = STRUCTURAL_ROOT / "projects"
        if projects_dir.exists():
            for proj in sorted(projects_dir.iterdir()):
                if not proj.is_dir() or proj.name.startswith("_"):
                    continue
                out_dir = proj / "output"
                if out_dir.exists() and find_tex_file(out_dir):
                    slug = f"sr_{proj.name}"
                    papers.append(
                        PaperSource(slug, out_dir, STRUCTURAL_ROOT, "structural", proj.name)
                    )

    return papers


def find_tex_file(slug_dir: Path) -> Path | None:
    v2 = slug_dir / "main_v2.tex"
    if v2.exists():
        return v2
    v1 = slug_dir / "main.tex"
    if v1.exists():
        return v1
    return None


def find_pdf(slug_dir: Path, tex_name: str) -> Path | None:
    pdf = slug_dir / tex_name.replace(".tex", ".pdf")
    return pdf if pdf.exists() else None


def _clean_title(tex: str) -> str:
    """Strip LaTeX line-break markers and extraneous whitespace from a title."""
    import re

    cleaned = tex
    cleaned = re.sub(r"\\\\\s*\\large\s*", " ", cleaned)
    cleaned = re.sub(r"\\\\[\s]*", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def build_meta_stub(
    slug: str,
    tex_path: Path,
    parsed: latex_parse.ParsedPaper,
    source_hash: str,
    root: Path,
) -> dict:
    pdf = find_pdf(tex_path.parent, tex_path.name)
    clean_title = _clean_title(parsed.title_tex)
    return {
        "slug": slug,
        "source": {
            "tex_path": str(tex_path.relative_to(root)).replace("\\", "/"),
            "pdf_path": str(pdf.relative_to(root)).replace("\\", "/") if pdf else None,
            "source_hash": source_hash,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        },
        "title": {"en": clean_title, "zh": ""},
        "short_title": {"en": clean_title, "zh": ""},
        "author": parsed.author_tex,
        "date": parsed.date_tex,
        "status": "draft",
        "abstract": {"tex": parsed.abstract_tex, "en": "", "zh": ""},
        "domain": [],
        "math_tools": [],
        "prerequisites": [],
        "main_theorems": [
            {
                "id": t.id,
                "env": t.env,
                "statement_tex": t.statement_tex,
                "section_number": t.section_number,
                "label": {"en": "", "zh": ""},
                "key_ideas": {"en": [], "zh": []},
            }
            for t in parsed.theorems
        ],
        "sections": [
            {"number": s.number, "title_tex": s.title_tex} for s in parsed.sections
        ],
        "related_papers": [],
        "figures": [{"path": f, "caption_tex": ""} for f in parsed.figures],
        "generation": None,
    }


def _extract_quality(paper: PaperSource) -> dict:
    """Extract quality metrics based on repo type."""
    if paper.repo_type == "realresearch":
        return eval_extract.extract_quality_realresearch(
            paper.slug, paper.repo_root
        )
    elif paper.repo_type == "structural" and paper.project_id:
        return eval_extract.extract_quality_structural(
            paper.project_id, paper.repo_root
        )
    return {}


def ingest_one(paper: PaperSource, *, force: bool = False) -> str:
    slug = paper.slug
    tex_path = find_tex_file(paper.tex_dir)
    if not tex_path:
        return f"skip {slug}: no .tex"
    tex_text = tex_path.read_text(encoding="utf-8", errors="replace")
    h = latex_parse.source_hash(tex_text)
    out_dir = CONTENT_DIR / slug
    meta_path = out_dir / "meta.json"
    hash_path = out_dir / ".source_hash"

    if not force and meta_path.exists() and hash_path.exists():
        if hash_path.read_text(encoding="utf-8").strip() == h:
            return f"cached {slug}"

    parsed = latex_parse.parse_latex(tex_text)
    meta = build_meta_stub(slug, tex_path, parsed, h, paper.repo_root)
    meta["repo"] = paper.repo_type
    meta["repo_root"] = str(paper.repo_root).replace("\\", "/")
    meta["project_id"] = paper.project_id

    quality = _extract_quality(paper)
    if quality:
        meta["quality"] = quality

    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    hash_path.write_text(h, encoding="utf-8")
    return f"ingested {slug} ({len(parsed.theorems)} theorems, {len(parsed.sections)} sections, quality={bool(quality)})"


def update_papers_index() -> None:
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "papers": [],
    }
    for meta_file in sorted(CONTENT_DIR.glob("*/meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        one_liner = meta.get("abstract", {}).get("en") or meta.get("abstract", {}).get(
            "tex", ""
        )
        abstract = meta.get("abstract", {})
        one_liner_en = (abstract.get("en") or abstract.get("tex", ""))[:180]
        one_liner_zh = (abstract.get("zh") or "")[:180]
        quality = meta.get("quality", {})
        index["papers"].append(
            {
                "slug": meta["slug"],
                "short_title": meta["short_title"],
                "status": meta["status"],
                "domain": meta["domain"],
                "math_tools": meta["math_tools"],
                "one_liner": {"en": one_liner_en, "zh": one_liner_zh},
                "repo": meta.get("repo", "realresearch"),
                "quality": {
                    "tier": quality.get("tier"),
                    "significance_score": quality.get("significance_score"),
                    "significance_max": quality.get("significance_max", 16),
                } if quality else None,
            }
        )
    (CONTENT_DIR / "papers.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None, help="Ingest only this slug")
    ap.add_argument("--force", action="store_true", help="Ignore hash cache")
    args = ap.parse_args(argv)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    all_papers = discover_papers()

    if args.slug:
        all_papers = [p for p in all_papers if p.slug == args.slug]
        if not all_papers:
            print(f"slug not found: {args.slug}", file=sys.stderr)
            return 1

    for paper in all_papers:
        try:
            print(ingest_one(paper, force=args.force))
        except Exception as e:
            print(f"error {paper.slug}: {e}", file=sys.stderr)
    update_papers_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
