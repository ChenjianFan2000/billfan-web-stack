#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import pipeline
from app.db import connect_db, init_db


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    return cleaned or "paper.pdf"


def _existing_file_names(db_path: str, user_id: int) -> set:
    with connect_db(db_path) as db:
        rows = db.execute(
            "SELECT file_path FROM papers WHERE user_id = ? AND file_path IS NOT NULL",
            (int(user_id),),
        ).fetchall()
    names = set()
    for row in rows:
        names.add(Path(row[0]).name)
    return names


def _normalize_stem(stem: str) -> str:
    return re.sub(r"_\d+$", "", stem)


def _copy_pdf(src: Path, dest_dir: Path, occupied_names: set) -> Path:
    base = _safe_filename(src.name)
    target = dest_dir / base
    stem = target.stem
    suffix = target.suffix or ".pdf"
    idx = 1
    while target.name in occupied_names or target.exists():
        target = dest_dir / f"{stem}_{idx}{suffix}"
        idx += 1

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, target)
    occupied_names.add(target.name)
    return target


def _collect_pdfs(zip_path: Path, extract_dir: Path) -> List[Path]:
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    extracted: List[Path] = []
    used_names: set = set()
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = str(info.filename or "")
            if not name.lower().endswith(".pdf"):
                continue
            rel_parts = [part for part in Path(name).parts if part]
            if rel_parts and rel_parts[0] == "__MACOSX":
                continue
            base = Path(name).name
            if base.startswith("._"):
                continue

            safe_base = _safe_filename(base)
            stem = Path(safe_base).stem or "paper"
            suffix = Path(safe_base).suffix or ".pdf"
            final_name = safe_base
            idx = 1
            while final_name in used_names:
                final_name = f"{stem}_{idx}{suffix}"
                idx += 1
            used_names.add(final_name)
            target = extract_dir / final_name

            with zf.open(info, "r") as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)

    return sorted(extracted)


def _print_queue(rows: List[Dict[str, object]]) -> None:
    print("Queue:")
    for item in rows:
        print(f"  #{item['queue_no']:>3} | {item['name']}")


def import_zip(
    zip_path: Path,
    extract_dir: Path,
    db_path: str,
    pdf_dir: Path,
    text_dir: Path,
    max_files: int = 0,
    skip_existing: bool = True,
    user_id: int = 1,
    start_index: int = 1,
) -> None:
    pdf_candidates = _collect_pdfs(zip_path, extract_dir)
    if not pdf_candidates:
        raise RuntimeError(f"zip has no PDFs: {zip_path}")

    occupied = _existing_file_names(db_path, user_id=user_id)
    imported_stems = {_normalize_stem(Path(name).stem) for name in occupied}

    queue_rows: List[Dict[str, object]] = []
    for src_pdf in pdf_candidates:
        normalized_src_stem = _normalize_stem(Path(_safe_filename(src_pdf.name)).stem)
        if skip_existing and normalized_src_stem in imported_stems:
            continue
        queue_rows.append({"queue_no": len(queue_rows) + 1, "name": src_pdf.name, "src": str(src_pdf)})
        imported_stems.add(normalized_src_stem)
        if max_files > 0 and len(queue_rows) >= max_files:
            break

    if not queue_rows:
        print("No new PDFs to import.")
        return

    start_index = max(1, int(start_index))
    if start_index > 1:
        queue_rows = queue_rows[start_index - 1 :]
        if not queue_rows:
            print("No PDFs left after start-index filter.")
            return

    _print_queue(queue_rows)

    ok = 0
    failed = 0

    for idx, item in enumerate(queue_rows, start=1):
        src_pdf = Path(item["src"])
        stored_pdf = _copy_pdf(src_pdf, pdf_dir, occupied)

        with connect_db(db_path) as db:
            paper_id = db.execute(
                "INSERT INTO papers (user_id, file_path) VALUES (?, ?)",
                (int(user_id), str(stored_pdf)),
            ).lastrowid
            job_id = db.execute(
                "INSERT INTO processing_jobs (user_id, paper_id, status) VALUES (?, ?, ?)",
                (int(user_id), paper_id, "pending"),
            ).lastrowid
            db.commit()

        print(f"[QUEUE {idx}/{len(queue_rows)}] {src_pdf.name} -> paper_id={paper_id}, job_id={job_id}", flush=True)
        try:
            pipeline.process_pdf_job(
                db_path=db_path,
                paper_id=paper_id,
                job_id=job_id,
                pdf_path=str(stored_pdf),
                user_id=int(user_id),
                texts_dir=str(text_dir),
            )
            ok += 1
            print(f"  [DONE] job_id={job_id}", flush=True)
        except Exception as exc:
            failed += 1
            print(f"  [ERR] job_id={job_id}, error={exc}", flush=True)

    print(f"Import complete: queued={len(queue_rows)}, success={ok}, failed={failed}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import PDFs from a zip file into the app database")
    parser.add_argument("--zip", dest="zip_path", default="/root/tmp/papers.zip", help="Path to zip containing PDFs")
    parser.add_argument("--extract-dir", default="/tmp/papers_import", help="Temporary extract directory")
    parser.add_argument("--db-path", default=os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite"))
    parser.add_argument("--pdf-dir", default=os.getenv("APP_PDFS_DIR", "/var/www/data/pdfs"))
    parser.add_argument("--text-dir", default=os.getenv("APP_TEXTS_DIR", "/var/www/data/texts"))
    parser.add_argument("--max-files", type=int, default=0, help="Process at most N files (0 means no limit)")
    parser.add_argument("--no-skip-existing", action="store_true", help="Do not skip already imported files")
    parser.add_argument("--user-id", type=int, default=1, help="Import as this user id")
    parser.add_argument("--start-index", type=int, default=1, help="Start from Nth item in queue (1-based)")
    args = parser.parse_args()

    zip_path = Path(args.zip_path)
    extract_dir = Path(args.extract_dir)
    db_path = args.db_path
    pdf_dir = Path(args.pdf_dir)
    text_dir = Path(args.text_dir)

    if not zip_path.exists():
        raise FileNotFoundError(f"zip not found: {zip_path}")

    init_db(db_path)
    import_zip(
        zip_path=zip_path,
        extract_dir=extract_dir,
        db_path=db_path,
        pdf_dir=pdf_dir,
        text_dir=text_dir,
        max_files=max(0, int(args.max_files)),
        skip_existing=not bool(args.no_skip_existing),
        user_id=int(args.user_id),
        start_index=max(1, int(args.start_index)),
    )


if __name__ == "__main__":
    main()
