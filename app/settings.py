from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.db import get_db
from app.settings_store import (
    CLASSIFICATION_GUIDANCE_KEY,
    DEFAULT_CLASSIFICATION_GUIDANCE,
    ensure_default_settings,
    get_setting_value,
    upsert_setting_value,
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


class ClassificationGuidancePayload(BaseModel):
    content: str = Field(default="", max_length=12000)


@router.get("/classification-guidance")
def get_classification_guidance(_user=Depends(get_current_user), db=Depends(get_db)):
    ensure_default_settings(db, user_id=int(_user["id"]))
    value = get_setting_value(
        db,
        CLASSIFICATION_GUIDANCE_KEY,
        default=DEFAULT_CLASSIFICATION_GUIDANCE,
        user_id=int(_user["id"]),
    )
    db.commit()
    return {"content": value}


@router.put("/classification-guidance")
def update_classification_guidance(payload: ClassificationGuidancePayload, _user=Depends(get_current_user), db=Depends(get_db)):
    value = payload.content.strip()
    upsert_setting_value(db, CLASSIFICATION_GUIDANCE_KEY, value, user_id=int(_user["id"]))
    db.commit()
    return {"content": value}
