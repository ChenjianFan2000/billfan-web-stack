from typing import Any, Dict, Iterable, List, Optional, Sequence


def normalize_category_ids(raw_ids: Optional[Iterable[Any]]) -> List[int]:
    if raw_ids is None:
        return []

    seen = set()
    normalized: List[int] = []
    for raw in raw_ids:
        if isinstance(raw, bool):
            raise ValueError("category id must be integer")
        try:
            category_id = int(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError("category id must be integer") from exc
        if category_id <= 0:
            raise ValueError("category id must be positive")
        if category_id in seen:
            continue
        seen.add(category_id)
        normalized.append(category_id)
    return normalized


def missing_category_ids(db, category_ids: Sequence[int], user_id: Optional[int] = None) -> List[int]:
    ids = [int(cid) for cid in category_ids]
    if not ids:
        return []

    placeholders = ",".join(["?"] * len(ids))
    if user_id is None:
        rows = db.execute(
            "SELECT id FROM categories WHERE id IN ({})".format(placeholders),
            tuple(ids),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT id FROM categories WHERE user_id = ? AND id IN ({})".format(placeholders),
            tuple([int(user_id)] + ids),
        ).fetchall()
    existing = {int(row["id"]) for row in rows}
    return [cid for cid in ids if cid not in existing]


def set_paper_categories(db, paper_id: int, category_ids: Sequence[int]) -> None:
    normalized = normalize_category_ids(category_ids)
    db.execute("DELETE FROM paper_categories WHERE paper_id = ?", (paper_id,))
    if normalized:
        db.executemany(
            "INSERT INTO paper_categories (paper_id, category_id) VALUES (?, ?)",
            [(paper_id, cid) for cid in normalized],
        )

    primary = normalized[0] if normalized else None
    db.execute("UPDATE papers SET category_id = ? WHERE id = ?", (primary, paper_id))


def fetch_paper_category_ids_map(
    db,
    paper_ids: Sequence[int],
    user_id: Optional[int] = None,
) -> Dict[int, List[int]]:
    ids = [int(pid) for pid in paper_ids]
    if not ids:
        return {}

    placeholders = ",".join(["?"] * len(ids))
    if user_id is None:
        category_rows = db.execute(
            """
            SELECT pc.paper_id, pc.category_id
            FROM paper_categories pc
            LEFT JOIN categories c ON c.id = pc.category_id
            WHERE pc.paper_id IN ({})
            ORDER BY COALESCE(c.order_index, 999999), pc.category_id
            """.format(placeholders),
            tuple(ids),
        ).fetchall()
        legacy_rows = db.execute(
            "SELECT id, category_id FROM papers WHERE id IN ({})".format(placeholders),
            tuple(ids),
        ).fetchall()
    else:
        category_rows = db.execute(
            """
            SELECT pc.paper_id, pc.category_id
            FROM paper_categories pc
            JOIN papers p ON p.id = pc.paper_id
            JOIN categories c ON c.id = pc.category_id
            WHERE p.user_id = ?
              AND c.user_id = ?
              AND pc.paper_id IN ({})
            ORDER BY COALESCE(c.order_index, 999999), pc.category_id
            """.format(placeholders),
            tuple([int(user_id), int(user_id)] + ids),
        ).fetchall()
        legacy_rows = db.execute(
            "SELECT id, category_id FROM papers WHERE user_id = ? AND id IN ({})".format(placeholders),
            tuple([int(user_id)] + ids),
        ).fetchall()

    result: Dict[int, List[int]] = {pid: [] for pid in ids}
    for row in category_rows:
        result[int(row["paper_id"])].append(int(row["category_id"]))

    for row in legacy_rows:
        paper_id = int(row["id"])
        legacy_category_id = row["category_id"]
        if legacy_category_id is None:
            continue
        legacy = int(legacy_category_id)
        current = result.get(paper_id)
        if current is None:
            result[paper_id] = [legacy]
            continue
        if legacy in current:
            current.remove(legacy)
        current.insert(0, legacy)

    return result


def fetch_paper_category_ids(db, paper_id: int, user_id: Optional[int] = None) -> List[int]:
    return fetch_paper_category_ids_map(db, [int(paper_id)], user_id=user_id).get(int(paper_id), [])


def category_direct_paper_counts(db, user_id: Optional[int] = None) -> Dict[int, int]:
    if user_id is None:
        rows = db.execute(
            """
            SELECT category_id, COUNT(*) AS cnt
            FROM (
                SELECT pc.paper_id, pc.category_id
                FROM paper_categories pc
                UNION
                SELECT p.id AS paper_id, p.category_id
                FROM papers p
                WHERE p.category_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM paper_categories pc
                      WHERE pc.paper_id = p.id AND pc.category_id = p.category_id
                  )
            )
            GROUP BY category_id
            """
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT category_id, COUNT(*) AS cnt
            FROM (
                SELECT pc.paper_id, pc.category_id
                FROM paper_categories pc
                JOIN papers p ON p.id = pc.paper_id
                JOIN categories c ON c.id = pc.category_id
                WHERE p.user_id = ?
                  AND COALESCE(p.is_quarantined, 0) = 0
                  AND c.user_id = ?
                UNION
                SELECT p.id AS paper_id, p.category_id
                FROM papers p
                JOIN categories c2 ON c2.id = p.category_id
                WHERE p.user_id = ?
                  AND COALESCE(p.is_quarantined, 0) = 0
                  AND c2.user_id = ?
                  AND p.category_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM paper_categories pc
                      WHERE pc.paper_id = p.id AND pc.category_id = p.category_id
                  )
            )
            GROUP BY category_id
            """,
            (int(user_id), int(user_id), int(user_id), int(user_id)),
        ).fetchall()
    return {int(row["category_id"]): int(row["cnt"]) for row in rows}


def category_has_papers(db, category_id: int, user_id: Optional[int] = None) -> bool:
    if user_id is None:
        linked = db.execute(
            "SELECT 1 FROM paper_categories WHERE category_id = ? LIMIT 1",
            (category_id,),
        ).fetchone()
    else:
        linked = db.execute(
            """
            SELECT 1
            FROM paper_categories pc
            JOIN papers p ON p.id = pc.paper_id
            WHERE pc.category_id = ?
              AND p.user_id = ?
            LIMIT 1
            """,
            (category_id, int(user_id)),
        ).fetchone()
    if linked is not None:
        return True

    if user_id is None:
        legacy = db.execute(
            """
            SELECT 1
            FROM papers p
            WHERE p.category_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM paper_categories pc
                  WHERE pc.paper_id = p.id AND pc.category_id = p.category_id
              )
            LIMIT 1
            """,
            (category_id,),
        ).fetchone()
    else:
        legacy = db.execute(
            """
            SELECT 1
            FROM papers p
            WHERE p.user_id = ?
              AND p.category_id = ?
              AND NOT EXISTS (
                  SELECT 1 FROM paper_categories pc
                  WHERE pc.paper_id = p.id AND pc.category_id = p.category_id
              )
            LIMIT 1
            """,
            (int(user_id), category_id),
        ).fetchone()
    return legacy is not None
