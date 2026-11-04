"""Pydantic schemas mirroring the on-disk JSON shapes for API responses."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class LocalizedStr(BaseModel):
    zh: str = ""
    en: str = ""


class PaperSummary(BaseModel):
    slug: str
    short_title: LocalizedStr
    status: str
    domain: list[str]
    math_tools: list[str]
    one_liner: str = ""


class PaperIndex(BaseModel):
    generated_at: str
    papers: list[PaperSummary]


class PaperContent(BaseModel):
    zh: str = ""
    en: str = ""


class PaperDetail(BaseModel):
    meta: dict[str, Any]
    content: PaperContent


class TagEntry(BaseModel):
    label: LocalizedStr
    papers: list[str]


class TagIndex(BaseModel):
    domains: dict[str, TagEntry]
    math_tools: dict[str, TagEntry]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    paper_slug: str
    message: str
    history: list[ChatMessage] = []
    lang: str = "zh"
    current_section: str | None = None


class HealthResponse(BaseModel):
    status: str
    papers_count: int
