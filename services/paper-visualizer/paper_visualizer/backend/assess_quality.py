"""Run a unified AI-based quality assessment on all papers.

For papers that already have quality data from the MATHPROVER pipeline
(scratchpad-extracted), this PRESERVES the pipeline data and only fills
in missing fields. For papers with NO quality data, it runs a full
AI assessment.

Usage:
    python -m paper_visualizer.backend.assess_quality
    python -m paper_visualizer.backend.assess_quality --slug sr_p001 --force
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from paper_visualizer.backend import vector_client
from paper_visualizer.backend.generate import CONTENT_DIR, _model, _load_tex

ASSESS_PROMPT = """You are a senior referee for mathematical research journals.
Evaluate the following paper on 5 dimensions using this rubric:

DIMENSIONS (rate each as "weak", "acceptable", or "strong"):
1. **correctness** — Are proofs complete? Are there gaps, hand-waving, or unverified claims?
2. **rigor** — Is every step justified? Are constants explicit? Are all hypotheses listed?
3. **novelty** — Is this a routine extension, a new technique, or a surprising result?
4. **framing** — Is the motivation clear? Does the abstract match what is proved? Are recent references cited?
5. **coherence** — Is notation consistent? Are there contradictions between sections?

Also assess:
- **significance_score** (0–16): How significant is the contribution? 0=trivial, 8=solid incremental, 12=strong contribution, 16=breakthrough.
- **tier**: "A" (coursework-level, single-tool), "B" (specialized journal, non-trivial depth), or "C" (top venue, all dimensions strong).
- **critic_verdict**: "PASS" if publishable with minor fixes, "PASS_WITH_MAJOR" if needs substantial revision, "FAIL" if fundamentally flawed.
- **one_sentence**: A one-sentence summary of the paper's main contribution.

Output ONLY a JSON object matching this schema (no prose, no code fences):

{
  "tier": "A|B|C",
  "significance_score": <int 0-16>,
  "critic_verdict": "PASS|PASS_WITH_MAJOR|FAIL",
  "dimensions": {
    "correctness": "weak|acceptable|strong",
    "rigor": "weak|acceptable|strong",
    "novelty": "weak|acceptable|strong",
    "framing": "weak|acceptable|strong",
    "coherence": "weak|acceptable|strong"
  },
  "one_sentence_zh": "<one sentence in Chinese>",
  "one_sentence_en": "<one sentence in English>"
}
"""


def assess_one(slug: str, *, force: bool = False) -> str:
    meta_path = CONTENT_DIR / slug / "meta.json"
    if not meta_path.exists():
        return f"skip {slug}: no meta.json"

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    existing = meta.get("quality", {})

    # Skip if already has tier + significance + dimensions (from pipeline)
    has_full = (
        existing.get("tier")
        and existing.get("significance_score") is not None
        and existing.get("dimensions")
    )
    if has_full and not force:
        return f"cached {slug} (pipeline data present)"

    # Load tex
    try:
        tex_body = _load_tex(meta)[:60000]
    except Exception as e:
        return f"skip {slug}: {e}"

    title = meta.get("title", {}).get("en", slug)
    abstract = meta.get("abstract", {}).get("tex", "")[:3000]

    resp = vector_client.chat(
        model=_model(),
        messages=[
            {"role": "system", "content": ASSESS_PROMPT},
            {
                "role": "user",
                "content": f"TITLE: {title}\n\nABSTRACT:\n{abstract}\n\nSOURCE (first 60k chars):\n{tex_body}",
            },
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    from paper_visualizer.backend.generate import _repair_json

    repaired = _repair_json(resp)
    try:
        result = json.loads(repaired)
    except json.JSONDecodeError as e:
        return f"error {slug}: JSON parse: {e}"

    # Merge: pipeline data takes precedence, AI fills gaps
    quality = dict(existing)
    quality.setdefault("tier", result.get("tier"))
    quality.setdefault("significance_score", result.get("significance_score"))
    quality.setdefault("significance_max", 16)
    quality.setdefault("critic_verdict", result.get("critic_verdict"))
    quality.setdefault("dimensions", result.get("dimensions"))
    quality["assessed_by"] = "unified_critic"

    meta["quality"] = quality

    # Also fill abstract.zh if missing (use the AI's one_sentence)
    if not meta.get("abstract", {}).get("zh") and result.get("one_sentence_zh"):
        meta.setdefault("abstract", {})["zh"] = result["one_sentence_zh"]

    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"assessed {slug}: tier={quality.get('tier')} sig={quality.get('significance_score')}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--force", action="store_true", help="Re-assess even if pipeline data exists")
    args = ap.parse_args(argv)

    slugs = (
        [args.slug]
        if args.slug
        else [p.parent.name for p in sorted(CONTENT_DIR.glob("*/meta.json"))]
    )
    for slug in slugs:
        try:
            print(assess_one(slug, force=args.force))
        except Exception as e:
            print(f"error {slug}: {e}", file=sys.stderr)

    # Rebuild index
    from paper_visualizer.backend import ingest

    ingest.update_papers_index()
    return 0


if __name__ == "__main__":
    sys.exit(main())
