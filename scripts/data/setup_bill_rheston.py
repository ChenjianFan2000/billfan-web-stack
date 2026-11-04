#!/usr/bin/env python3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import _password_hash
from app.db import connect_db, init_db
from app.settings_store import CLASSIFICATION_GUIDANCE_KEY, upsert_setting_value

USERNAME = "bill_rheston"
PASSWORD = "jclcgs"
CATEGORIES = [
    "Markovian Approximation",
    "Rational Approximation",
    "Adams",
    "PPDE",
    "deep",
    "基础理论",
    "其他算法",
    "杂项",
]
GUIDANCE = (
    "根据论文使用的rough Heston算法分类到各个类别，如并不涉及rHeston的具体算法但是是模型或某种算法所用"
    "理论的基础知识，则同时归类到基础理论和对应的算法。如所用算法并不属于上述五大类，则归类于其他算法。"
    "注意，Lifted Heston是rough Heston的Markovian Approximation后的模型，基于其开发的类似于Nicola的CLP算法"
    "归于其他算法，而非Markovian。如某篇归在哪里都不合适，则归入杂项。"
)


def main() -> None:
    db_path = os.getenv("APP_DB_PATH", "/var/www/data/db.sqlite")
    init_db(db_path)

    with connect_db(db_path) as db:
        user = db.execute("SELECT id FROM users WHERE username = ?", (USERNAME,)).fetchone()
        pwd_hash = _password_hash(PASSWORD)
        if user is None:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (USERNAME, pwd_hash),
            )
            print(f"[OK] created user: {USERNAME}")
        else:
            db.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (pwd_hash, USERNAME),
            )
            print(f"[OK] reset password for existing user: {USERNAME}")

        for idx, name in enumerate(CATEGORIES):
            row = db.execute("SELECT id FROM categories WHERE name = ? ORDER BY id ASC LIMIT 1", (name,)).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO categories (name, parent_id, order_index) VALUES (?, NULL, ?)",
                    (name, idx),
                )
                print(f"[OK] created category: {name}")
            else:
                db.execute(
                    "UPDATE categories SET parent_id = NULL, order_index = ? WHERE id = ?",
                    (idx, int(row["id"])),
                )
                print(f"[OK] updated category order: {name}")

        upsert_setting_value(db, CLASSIFICATION_GUIDANCE_KEY, GUIDANCE)
        db.commit()
        print("[OK] classification guidance saved")


if __name__ == "__main__":
    main()
