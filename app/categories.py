from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.db import get_db
from app.logger import log_operation
from app.paper_categories import category_direct_paper_counts, category_has_papers

router = APIRouter(prefix="/api/categories", tags=["categories"])


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    parent_id: Optional[int] = None
    order_index: int = 0


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    parent_id: Optional[int] = None
    order_index: Optional[int] = None


def _get_category_row(db, category_id: int, user_id: int):
    return db.execute(
        "SELECT id, name, parent_id, order_index FROM categories WHERE id = ? AND user_id = ?",
        (category_id, int(user_id)),
    ).fetchone()


def _validate_parent_for_one_level(
    db,
    parent_id: Optional[int],
    user_id: int,
    current_category_id: Optional[int] = None,
) -> None:
    if parent_id is None:
        return

    if current_category_id is not None and parent_id == current_category_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot set self as parent")

    parent = _get_category_row(db, parent_id, user_id=user_id)
    if parent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parent category not found")

    # One-level hierarchy: parent must be a root node.
    if parent["parent_id"] is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="only one-level nesting is allowed",
        )


def _has_children(db, category_id: int, user_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM categories WHERE parent_id = ? AND user_id = ? LIMIT 1",
        (category_id, int(user_id)),
    ).fetchone()
    return row is not None


def _category_direct_paper_counts(db, user_id: int) -> Dict[int, int]:
    return category_direct_paper_counts(db, user_id=user_id)


def _build_category_tree(rows, counts: Dict[int, int]) -> List[Dict]:
    nodes = {
        row["id"]: {
            "id": row["id"],
            "name": row["name"],
            "parent_id": row["parent_id"],
            "order_index": row["order_index"],
            "count": int(counts.get(row["id"], 0)),
            "children": [],
        }
        for row in rows
    }

    roots: List[Dict] = []
    for node in nodes.values():
        parent_id = node["parent_id"]
        if parent_id is None:
            roots.append(node)
        elif parent_id in nodes:
            nodes[parent_id]["children"].append(node)

    def sort_nodes(items: List[Dict]) -> None:
        items.sort(key=lambda x: (x["order_index"], x["id"]))
        for item in items:
            sort_nodes(item["children"])

    sort_nodes(roots)
    return roots


@router.get("")
def list_categories(_user=Depends(get_current_user), db=Depends(get_db)):
    rows = db.execute(
        "SELECT id, name, parent_id, order_index FROM categories WHERE user_id = ? ORDER BY order_index ASC, id ASC",
        (int(_user["id"]),),
    ).fetchall()
    if not rows:
        return []

    counts = _category_direct_paper_counts(db, user_id=int(_user["id"]))
    return _build_category_tree(rows, counts)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreateRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name cannot be blank")

    _validate_parent_for_one_level(db, payload.parent_id, user_id=int(_user["id"]))

    cur = db.execute(
        "INSERT INTO categories (user_id, name, parent_id, order_index) VALUES (?, ?, ?, ?)",
        (int(_user["id"]), name, payload.parent_id, payload.order_index),
    )
    db.commit()

    category_id = cur.lastrowid
    row = _get_category_row(db, category_id, user_id=int(_user["id"]))
    log_operation(
        db,
        operation="category_edit",
        entity_type="category",
        entity_id=category_id,
        detail={"action": "create", "name": row["name"], "parent_id": row["parent_id"], "order_index": row["order_index"]},
        status="success",
        message="category created",
        user_id=int(_user["id"]),
    )
    return {
        "id": row["id"],
        "name": row["name"],
        "parent_id": row["parent_id"],
        "order_index": row["order_index"],
    }


@router.put("/{category_id}")
def update_category(category_id: int, payload: CategoryUpdateRequest, _user=Depends(get_current_user), db=Depends(get_db)):
    row = _get_category_row(db, category_id, user_id=int(_user["id"]))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")

    new_name = payload.name.strip() if payload.name is not None else row["name"]
    if not new_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="name cannot be blank")

    if "parent_id" in payload.__fields_set__:
        new_parent_id = payload.parent_id
    else:
        new_parent_id = row["parent_id"]

    new_order_index = payload.order_index if payload.order_index is not None else row["order_index"]

    _validate_parent_for_one_level(
        db,
        new_parent_id,
        user_id=int(_user["id"]),
        current_category_id=category_id,
    )

    # If this category has children, it must remain root to keep one-level nesting.
    if new_parent_id is not None and _has_children(db, category_id, user_id=int(_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="category with children cannot become child",
        )

    db.execute(
        "UPDATE categories SET name = ?, parent_id = ?, order_index = ? WHERE id = ? AND user_id = ?",
        (new_name, new_parent_id, new_order_index, category_id, int(_user["id"])),
    )
    db.commit()
    log_operation(
        db,
        operation="category_edit",
        entity_type="category",
        entity_id=category_id,
        detail={
            "action": "update",
            "old": {"name": row["name"], "parent_id": row["parent_id"], "order_index": row["order_index"]},
            "new": {"name": new_name, "parent_id": new_parent_id, "order_index": new_order_index},
        },
        status="success",
        message="category updated",
        user_id=int(_user["id"]),
    )

    updated = _get_category_row(db, category_id, user_id=int(_user["id"]))
    return {
        "id": updated["id"],
        "name": updated["name"],
        "parent_id": updated["parent_id"],
        "order_index": updated["order_index"],
    }


@router.delete("/{category_id}")
def delete_category(category_id: int, _user=Depends(get_current_user), db=Depends(get_db)):
    row = _get_category_row(db, category_id, user_id=int(_user["id"]))
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="category not found")

    if _has_children(db, category_id, user_id=int(_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="category has child categories",
        )

    if category_has_papers(db, category_id, user_id=int(_user["id"])):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="category has papers",
        )

    db.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, int(_user["id"])))
    db.commit()
    log_operation(
        db,
        operation="category_edit",
        entity_type="category",
        entity_id=category_id,
        detail={"action": "delete", "name": row["name"]},
        status="success",
        message="category deleted",
        user_id=int(_user["id"]),
    )
    return {"ok": True}
