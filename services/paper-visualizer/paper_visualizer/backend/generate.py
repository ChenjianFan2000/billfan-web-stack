"""Call VectorEngine to produce bilingual teaching Markdown per paper,
then rebuild papers.json and tags.json.

Usage:
    python -m paper_visualizer.backend.generate
    python -m paper_visualizer.backend.generate --slug project8 --force --lang zh
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from paper_visualizer.backend import ingest as ingest_mod
from paper_visualizer.backend import prompts, vector_client

CONTENT_DIR = ingest_mod.CONTENT_DIR
ROOT = ingest_mod.ROOT
TEX_LIMIT = 60_000
LANG_NAMES = {"zh": "Chinese (中文)", "en": "English"}


def _model() -> str:
    return os.environ.get("PAPER_VISUALIZER_MODEL", "gpt-5.4-pro")


def _load_meta(slug: str) -> dict:
    return json.loads((CONTENT_DIR / slug / "meta.json").read_text(encoding="utf-8"))


def _save_meta(slug: str, meta: dict) -> None:
    (CONTENT_DIR / slug / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_tex(meta: dict) -> str:
    repo_root = Path(meta.get("repo_root", str(ROOT)))
    path = repo_root / meta["source"]["tex_path"]
    return path.read_text(encoding="utf-8", errors="replace")


def _format_theorems(meta: dict) -> str:
    out = []
    for t in meta.get("main_theorems", []):
        stmt = t["statement_tex"][:600].replace("\n", " ")
        out.append(
            f"- [{t['id']}] ({t.get('env','theorem')}, section {t.get('section_number')}): {stmt}"
        )
    return "\n".join(out) if out else "(none detected)"


def _format_sections(meta: dict) -> str:
    return ", ".join(
        f"{s['number']} {s['title_tex']}" for s in meta.get("sections", [])
    )


def _all_slugs() -> list[str]:
    return sorted(p.parent.name for p in CONTENT_DIR.glob("*/meta.json"))


def generate_teach(meta: dict, tex_body: str, lang: str) -> str:
    user = prompts.TEACH_USER_TEMPLATE.format(
        lang_name=LANG_NAMES[lang],
        lang_code=lang,
        title=meta["title"].get("en", meta["slug"]),
        author=meta.get("author", ""),
        abstract=meta["abstract"]["tex"],
        theorems=_format_theorems(meta),
        sections=_format_sections(meta),
        related_slugs=", ".join(s for s in _all_slugs() if s != meta["slug"]),
        tex_limit=TEX_LIMIT,
        tex_body=tex_body[:TEX_LIMIT],
        slug=meta["slug"],
    )
    return vector_client.chat(
        model=_model(),
        messages=[
            {"role": "system", "content": prompts.TEACH_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=8000,
    )


def _repair_json(text: str) -> str:
    """Best-effort fix for the most common AI JSON bugs.

    Strip code fences, then run a character-level state machine that escapes
    ASCII double quotes that appear inside a string value (detected by looking
    ahead to see whether the quote is followed by a valid JSON continuation).
    """
    # Strip code fences
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip().rsplit("```", 1)[0]

    # First attempt: parse as-is.
    try:
        json.loads(stripped)
        return stripped
    except json.JSONDecodeError:
        pass

    # State-machine-based escape of inner quotes.
    n = len(stripped)
    out: list[str] = []
    i = 0
    in_string = False
    escape_next = False
    while i < n:
        c = stripped[i]
        if escape_next:
            out.append(c)
            escape_next = False
            i += 1
            continue
        if c == "\\":
            out.append(c)
            escape_next = True
            i += 1
            continue
        if c == '"':
            if not in_string:
                out.append(c)
                in_string = True
            else:
                # Possible end of string — look ahead to see if next non-whitespace
                # char is a valid JSON continuation (,  :  }  ]).
                j = i + 1
                while j < n and stripped[j] in " \t\r\n":
                    j += 1
                if j >= n or stripped[j] in ",:}]":
                    out.append(c)
                    in_string = False
                else:
                    # Inner quote — escape it
                    out.append("\\")
                    out.append(c)
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def generate_classify(meta: dict) -> dict:
    theorem_ids = [t["id"] for t in meta.get("main_theorems", [])]
    user = prompts.CLASSIFY_USER_TEMPLATE.format(
        title=meta["title"].get("en", meta["slug"]),
        abstract=meta["abstract"]["tex"][:3000],
        theorems=_format_theorems(meta)[:5000],
        sections=_format_sections(meta),
        all_slugs=", ".join(_all_slugs()),
        theorem_ids=", ".join(theorem_ids),
    )
    resp = vector_client.chat(
        model=_model(),
        messages=[
            {"role": "system", "content": prompts.CLASSIFY_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=3000,
    )
    repaired = _repair_json(resp)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        # Last-resort retry with the raw text stripped of ``` fences
        stripped = resp.strip()
        if stripped.startswith("```"):
            stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
            if stripped.rstrip().endswith("```"):
                stripped = stripped.rstrip().rsplit("```", 1)[0]
        return json.loads(stripped)


def patch_meta_with_classification(meta: dict, classification: dict) -> None:
    st = classification.get("short_title", meta.get("short_title", {}))
    meta["short_title"] = {
        "zh": st.get("zh", ""),
        "en": st.get("en", meta.get("short_title", {}).get("en", "")),
    }
    title_zh = classification.get("title_zh", "")
    if title_zh:
        meta["title"]["zh"] = title_zh
    abs_cls = classification.get("abstract", {})
    meta["abstract"]["zh"] = abs_cls.get("zh", "")
    meta["abstract"]["en"] = abs_cls.get("en", "")
    meta["domain"] = classification.get("domain", [])
    meta["math_tools"] = classification.get("math_tools", [])
    meta["prerequisites"] = classification.get("prerequisites", [])
    meta["related_papers"] = classification.get("related_papers", [])
    labels = {item["id"]: item for item in classification.get("main_theorems_labels", [])}
    for t in meta.get("main_theorems", []):
        lbl = labels.get(t["id"], {})
        t["label"] = {"zh": lbl.get("label_zh", ""), "en": lbl.get("label_en", "")}
        t["key_ideas"] = {
            "zh": lbl.get("key_ideas_zh", []),
            "en": lbl.get("key_ideas_en", []),
        }


def _missing_langs(slug: str, langs: list[str]) -> list[str]:
    return [lang for lang in langs if not (CONTENT_DIR / slug / f"{lang}.md").exists()]


def _prompt_version_outdated(meta: dict) -> bool:
    gen = meta.get("generation")
    if not gen:
        return True
    return gen.get("prompt_version") != prompts.PROMPT_VERSION


def generate_one(slug: str, *, force: bool = False, langs: list[str]) -> str:
    meta = _load_meta(slug)
    missing = _missing_langs(slug, langs)
    needs_classify = force or _prompt_version_outdated(meta) or not meta.get("domain")
    needs_teach = force or bool(missing)

    if not needs_teach and not needs_classify:
        return f"cached {slug}"

    tex_body = _load_tex(meta) if (needs_teach or needs_classify) else ""
    langs_to_write = langs if force else missing

    for lang in langs_to_write:
        md = generate_teach(meta, tex_body, lang)
        (CONTENT_DIR / slug / f"{lang}.md").write_text(md, encoding="utf-8")

    if needs_classify:
        try:
            cls = generate_classify(meta)
            patch_meta_with_classification(meta, cls)
        except Exception as e:
            print(f"warn {slug}: classify failed: {e}", file=sys.stderr)

    existing_langs = set(meta.get("generation", {}).get("langs", [])) if meta.get("generation") else set()
    all_langs = sorted(existing_langs.union(langs_to_write))
    meta["generation"] = {
        "model": _model(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompts.PROMPT_VERSION,
        "langs": all_langs,
    }
    _save_meta(slug, meta)
    return f"generated {slug} ({', '.join(langs_to_write)})"


def rebuild_tags() -> None:
    domains: dict[str, dict] = {}
    tools: dict[str, dict] = {}
    for meta_file in sorted(CONTENT_DIR.glob("*/meta.json")):
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        slug = meta["slug"]
        for d in meta.get("domain", []):
            entry = domains.setdefault(
                d, {"label": {"zh": d.replace("_", " "), "en": d.replace("_", " ")}, "papers": []}
            )
            if slug not in entry["papers"]:
                entry["papers"].append(slug)
        for t in meta.get("math_tools", []):
            entry = tools.setdefault(
                t, {"label": {"zh": t.replace("_", " "), "en": t.replace("_", " ")}, "papers": []}
            )
            if slug not in entry["papers"]:
                entry["papers"].append(slug)
    (CONTENT_DIR / "tags.json").write_text(
        json.dumps({"domains": domains, "math_tools": tools}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--lang", choices=["zh", "en", "both"], default="both")
    args = ap.parse_args(argv)

    langs = ["zh", "en"] if args.lang == "both" else [args.lang]
    slugs = (
        [args.slug]
        if args.slug
        else [p.parent.name for p in sorted(CONTENT_DIR.glob("*/meta.json"))]
    )
    for slug in slugs:
        try:
            print(generate_one(slug, force=args.force, langs=langs))
        except Exception as e:
            print(f"error {slug}: {e}", file=sys.stderr)

    ingest_mod.update_papers_index()
    rebuild_tags()
    return 0


if __name__ == "__main__":
    sys.exit(main())
