#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import connect_db, init_db
from app.paper_categories import fetch_paper_category_ids, set_paper_categories

MAIN_GROUPS = [
    "Markovian Approximation",
    "Rational Approximation",
    "Adams",
    "PPDE",
    "deep",
]
REQUIRED_GROUPS = MAIN_GROUPS + ["基础理论", "其他算法", "杂项"]


def _contains_any(text: str, keywords: List[str]) -> bool:
    source = text.lower()
    return any(keyword in source for keyword in keywords)


def _normalize_text(*parts: str) -> str:
    text = "\n".join([str(part or "") for part in parts])
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def _target_groups(text: str) -> List[str]:
    groups: List[str] = []

    markovian_hit = _contains_any(
        text,
        [
            "markovian approximation",
            "markovianized",
            "multi-factor heston",
            "multi factor heston",
            "lifted heston",
        ],
    )
    rational_hit = _contains_any(
        text,
        [
            "rational approximation",
            "fractional riccati",
            "rational kernel",
            "pade",
            "padé",
            "prony",
        ],
    )
    adams_hit = _contains_any(
        text,
        [
            "fractional adams",
            "adams-bashforth",
            "predictor-corrector",
            "predictor corrector",
            "adams method",
        ],
    )
    ppde_hit = _contains_any(
        text,
        [
            "ppde",
            "path-dependent pde",
            "path dependent pde",
            "functional ito",
            "viscosity solution",
        ],
    )
    deep_hit = _contains_any(
        text,
        [
            "deep learning",
            "neural network",
            "deep hedging",
            "reinforcement learning",
            "transformer",
            "diffusion model",
        ],
    )

    if markovian_hit:
        groups.append("Markovian Approximation")
    if rational_hit:
        groups.append("Rational Approximation")
    if adams_hit:
        groups.append("Adams")
    if ppde_hit:
        groups.append("PPDE")
    if deep_hit:
        groups.append("deep")

    lifted_clp_hit = "lifted heston" in text and _contains_any(text, ["clp", "nicola"])
    if lifted_clp_hit:
        groups = [name for name in groups if name != "Markovian Approximation"]
        if "其他算法" not in groups:
            groups.append("其他算法")

    other_algorithm_hit = _contains_any(
        text,
        [
            "monte carlo",
            "quasi-monte",
            "fourier",
            "fft",
            "finite difference",
            "runge-kutta",
            "runge kutta",
            "particle filter",
            "clp",
            "nicola",
            "calibration",
            "numerical scheme",
        ],
    )

    if not any(name in groups for name in MAIN_GROUPS) and other_algorithm_hit:
        groups.append("其他算法")

    theory_hit = _contains_any(
        text,
        [
            "rough heston model",
            "rough volatility",
            "fractional brownian",
            "volterra",
            "stochastic calculus",
            "malliavin",
            "existence",
            "uniqueness",
            "riccati-volterra",
            "mittag-leffler",
            "asymptotic",
        ],
    )

    if theory_hit and "基础理论" not in groups:
        groups.append("基础理论")

    if not groups:
        groups.append("杂项")

    # Keep order stable and unique
    ordered: List[str] = []
    seen: Set[str] = set()
    for name in MAIN_GROUPS + ["基础理论", "其他算法", "杂项"]:
        if name in groups and name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered


def main() -> None:
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    init_db(db_path)

    with connect_db(db_path) as db:
        rows = db.execute(
            """
            SELECT id, title, abstract_original, abstract_zh, summary_one_line, publisher
            FROM papers
            ORDER BY id ASC
            """
        ).fetchall()
        categories = db.execute("SELECT id, name FROM categories").fetchall()
        name_to_id: Dict[str, int] = {str(row["name"]): int(row["id"]) for row in categories}

        missing = [name for name in REQUIRED_GROUPS if name not in name_to_id]
        if missing:
            raise RuntimeError(f"missing required categories: {missing}")

        changed = 0
        for row in rows:
            paper_id = int(row["id"])
            merged_text = _normalize_text(
                row["title"],
                row["publisher"],
                row["summary_one_line"],
                row["abstract_original"],
                row["abstract_zh"],
            )
            target_names = _target_groups(merged_text)
            target_ids = [name_to_id[name] for name in target_names]

            current_ids = fetch_paper_category_ids(db, paper_id)
            if current_ids == target_ids:
                continue

            set_paper_categories(db, paper_id, target_ids)
            changed += 1
            print(f"[UPDATE] paper_id={paper_id} -> {target_names}")

        db.commit()
        print(f"Optimization complete: total={len(rows)}, updated={changed}, unchanged={len(rows) - changed}")


if __name__ == "__main__":
    main()
