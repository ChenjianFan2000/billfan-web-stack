"""Extract quality/evaluation metrics from scratchpad artifacts.

Reads significance scores, tier verdicts, critic verdicts, coherence verdicts,
and per-dimension assessments from the evaluation files that the MATHPROVER
pipeline produces during Phase 4.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


def _safe_yaml_load(path: Path) -> dict | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_significance_score(text: str) -> int | None:
    """Extract 'X/16' or 'X/14' significance score from markdown."""
    m = re.search(r"(?:score|significance)[:\s]*(\d{1,2})\s*/\s*(1[46])", text, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d{1,2})\s*/\s*16", text)
    if m:
        return int(m.group(1))
    return None


def _extract_tier(text: str) -> str | None:
    """Extract 'Tier A/B/C' from text — prefers verdict/classification lines,
    falls back to last occurrence (conclusions come last)."""
    # Prefer explicit verdict lines
    for pattern in [
        r"(?:verdict|classification|classified|recommend)[:\s]*[Tt]ier\s+([ABC])",
        r"[Tt]ier\s+([ABC])\s*\((?:confident|recommended|borderline)",
    ]:
        m = re.search(pattern, text, re.I)
        if m:
            return m.group(1)
    # Fall back to last occurrence
    matches = re.findall(r"[Tt]ier\s+([ABC])\b", text)
    return matches[-1] if matches else None


def _extract_verdict(text: str, keyword: str) -> str | None:
    """Extract a verdict like 'PASS', 'FAIL', 'PASS_WITH_MAJOR', etc."""
    pattern = rf"{keyword}[:\s]*(PASS_CLEAN|PASS_WITH_MAJOR|PASS_W/MAJOR|PASS|FAIL|MAJOR_ISSUES|MINOR_ISSUES|COHERENT|NOT_RUN)"
    m = re.search(pattern, text, re.I)
    if m:
        return m.group(1).upper().replace("W/", "WITH_")
    return None


def _extract_dimensions(text: str) -> dict[str, str]:
    """Extract per-dimension assessments (correctness: strong, etc.)."""
    dims: dict[str, str] = {}
    for dim in ["correctness", "rigor", "novelty", "framing", "coherence"]:
        m = re.search(
            rf"{dim}[:\s]*(strong|acceptable|weak)(?:\s*[-–—to]*\s*(strong|acceptable|weak))?",
            text,
            re.I,
        )
        if m:
            val = m.group(2) or m.group(1)
            dims[dim] = val.lower()
    return dims


def _extract_target_venues(text: str) -> list[str]:
    """Extract target journal names from evaluation text."""
    m = re.search(
        r"(?:target|venue|journal)[s]?[:\s]*((?:[\w\s&]+(?:,|;)\s*)*[\w\s&]+)",
        text,
        re.I,
    )
    if m:
        raw = m.group(1)
        venues = [v.strip() for v in re.split(r"[,;]", raw) if v.strip()]
        return [v for v in venues if len(v) > 3][:5]
    return []


def extract_quality_realresearch(slug: str, repo_root: Path) -> dict[str, Any]:
    """Extract quality metrics for a Realresearch paper."""
    quality: dict[str, Any] = {}
    scratchpad = repo_root / "scratchpad"

    # Check benchmark_calibration.yaml
    cal_path = repo_root / "knowledge" / "benchmark_calibration.yaml"
    if cal_path.exists():
        cal = _safe_yaml_load(cal_path)
        if cal and "anchor_set" in cal:
            anchors = cal["anchor_set"]
            positives = anchors.get("positives", []) if isinstance(anchors, dict) else anchors
            if isinstance(positives, list):
                for anchor in positives:
                    if not isinstance(anchor, dict):
                        continue
                    pid = anchor.get("paper_id") or anchor.get("slug") or ""
                    if pid == slug:
                        etier = anchor.get("expected_tier", "")
                        quality["tier"] = etier.replace("tier_", "").upper()
                        sig_text = anchor.get("rationale", "")
                        score = _extract_significance_score(sig_text)
                        if score is not None:
                            quality["significance_score"] = score

    # Tier evaluation gate (project7, project8)
    for tier_file in sorted(
        (scratchpad / slug).glob("tier_evaluation*.md")
        if (scratchpad / slug).exists()
        else []
    ):
        text = tier_file.read_text(encoding="utf-8", errors="replace")
        tier = _extract_tier(text)
        if tier:
            quality["tier"] = tier
        dims = _extract_dimensions(text)
        if dims:
            quality["dimensions"] = dims
        venues = _extract_target_venues(text)
        if venues:
            quality["target_venues"] = venues

    # Significance markdown
    for sig_file in sorted(scratchpad.glob(f"{slug}*significance*.md")):
        text = sig_file.read_text(encoding="utf-8", errors="replace")
        score = _extract_significance_score(text)
        if score is not None:
            quality["significance_score"] = score

    # Per-project scratchpad: tier_eval/ directory
    tier_eval_dir = scratchpad / slug / "tier_eval"
    if tier_eval_dir.exists():
        evidence_file = tier_eval_dir / "evidence.json"
        if evidence_file.exists():
            try:
                ev = json.loads(evidence_file.read_text(encoding="utf-8"))
                if "significance_score" in ev:
                    quality["significance_score"] = ev["significance_score"]
                if "critic_verdict" in ev:
                    quality["critic_verdict"] = ev["critic_verdict"]
                if "coherence_verdict" in ev:
                    quality["coherence_verdict"] = ev["coherence_verdict"]
            except Exception:
                pass

    # Significance critic round files (project7, project8)
    for sig_round in sorted(
        (scratchpad / slug).glob("significance_critic_round*.md")
        if (scratchpad / slug).exists()
        else []
    ):
        text = sig_round.read_text(encoding="utf-8", errors="replace")
        score = _extract_significance_score(text)
        if score is not None:
            quality["significance_score"] = score

    quality.setdefault("significance_max", 16)
    return quality


def extract_quality_structural(project_id: str, repo_root: Path) -> dict[str, Any]:
    """Extract quality metrics for a structural_research project."""
    quality: dict[str, Any] = {}
    scratchpad = repo_root / "projects" / project_id / "scratchpad"

    if not scratchpad.exists():
        return quality

    # Tier evaluation files
    for tier_file in sorted(scratchpad.glob("tier_evaluation*.md")):
        text = tier_file.read_text(encoding="utf-8", errors="replace")
        tier = _extract_tier(text)
        if tier:
            quality["tier"] = tier
        dims = _extract_dimensions(text)
        if dims:
            quality["dimensions"] = dims
        venues = _extract_target_venues(text)
        if venues:
            quality["target_venues"] = venues
        score = _extract_significance_score(text)
        if score is not None:
            quality["significance_score"] = score

    # Critic reviews
    for critic_file in sorted(scratchpad.glob("*critic_review*.md")):
        text = critic_file.read_text(encoding="utf-8", errors="replace")
        v = _extract_verdict(text, "(?:Critic|Overall|Verdict)")
        if v:
            quality["critic_verdict"] = v

    # Phase 0 critic
    for phase0 in sorted(scratchpad.glob("phase0_critic*.md")):
        text = phase0.read_text(encoding="utf-8", errors="replace")
        v = _extract_verdict(text, "(?:Verdict|Overall)")
        if v:
            quality["critic_verdict"] = v

    # Project config for phase info
    config_path = repo_root / "projects" / project_id / "config.yaml"
    if config_path.exists():
        cfg = _safe_yaml_load(config_path)
        if cfg:
            if "phase" in cfg:
                quality["phase"] = cfg["phase"]
            if "status" in cfg:
                quality["project_status"] = cfg["status"]

    quality.setdefault("significance_max", 16)
    return quality
