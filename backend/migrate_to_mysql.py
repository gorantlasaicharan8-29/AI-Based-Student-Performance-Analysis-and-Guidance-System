"""
migrate_to_mysql.py
Connects to MySQL, creates the database, all tables, and migrates
all data from the existing SQLite file into MySQL.
Run once: python migrate_to_mysql.py
"""

import sys
import os
import sqlite3
from urllib.parse import quote_plus

sys.path.insert(0, os.path.abspath('.'))

MYSQL_USER     = "root"
MYSQL_PASSWORD = "Root@2026#"
MYSQL_HOST     = "localhost"
MYSQL_PORT     = 3306
MYSQL_DB       = "student_performance_db"

# URL-encode password so special chars like @ and # don't break the connection
MYSQL_PASSWORD_ENCODED = quote_plus(MYSQL_PASSWORD)  # Root%402026%23

# ── Step 1: Create the database if it doesn't exist ───────────────────────────
print("\n" + "="*60)
print("  STEP 1 — Creating MySQL database...")
print("="*60)

import pymysql

conn = pymysql.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    charset="utf8mb4",
)
cursor = conn.cursor()
cursor.execute(f"DROP DATABASE IF EXISTS `{MYSQL_DB}`;")
cursor.execute(f"CREATE DATABASE `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
conn.commit()
cursor.close()
conn.close()
print(f"  [OK] Database '{MYSQL_DB}' ready.")

# ── Step 2: Create all tables via SQLAlchemy (Flask app) ──────────────────────
print("\n" + "="*60)
print("  STEP 2 — Creating tables in MySQL...")
print("="*60)

# Temporarily set env var so create_app uses MySQL
os.environ["DATABASE_URL"] = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_ENCODED}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
)

from app import create_app
from database import db

app = create_app()
with app.app_context():
    db.create_all()
print("  [OK] All tables created in MySQL.")

# ── Step 3: Migrate data from SQLite ─────────────────────────────────────────
print("\n" + "="*60)
print("  STEP 3 — Migrating data from SQLite...")
print("="*60)

SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_system.db")

if not os.path.exists(SQLITE_PATH):
    print("  [WARN] No SQLite database found. Skipping migration.")
    print("  The app will start fresh with MySQL.")
else:
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sc = sqlite_conn.cursor()

    mysql_conn = pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DB, charset="utf8mb4",
    )
    mc = mysql_conn.cursor()

    # Order matters for foreign keys
    TABLES = [
        "users", "students", "subjects", "marks",
        "units", "topics", "assignments", "submissions",
        "predictions", "notifications"
    ]

    total = 0
    for table in TABLES:
        sc.execute(f"SELECT * FROM {table}")
        rows = sc.fetchall()
        if not rows:
            print(f"  [SKIP] {table:<20} — empty")
            continue

        cols   = [d[0] for d in sc.description]
        placeholders = ", ".join(["%s"] * len(cols))
        col_names    = ", ".join([f"`{c}`" for c in cols])
        sql = f"INSERT IGNORE INTO `{table}` ({col_names}) VALUES ({placeholders})"

        count = 0
        for row in rows:
            values = []
            for v in row:
                if isinstance(v, bytes):
                    values.append(v.decode("utf-8", errors="replace"))
                else:
                    values.append(v)
            try:
                mc.execute(sql, values)
                count += 1
            except Exception as e:
                print(f"  [ERR] {table} row skipped: {e}")

        mysql_conn.commit()
        print(f"  [MIGRATED] {table:<20} — {count} rows")
        total += count

    sqlite_conn.close()
    mysql_conn.close()
    print(f"\n  [OK] Total {total} rows migrated to MySQL.")

# ── Step 4: Update config.py ─────────────────────────────────────────────────
print("\n" + "="*60)
print("  STEP 4 — Updating config.py to use MySQL...")
print("="*60)

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.py")
with open(config_path, "r") as f:
    content = f.read()

old_line = '    SQLALCHEMY_DATABASE_URI = os.getenv(\n        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, \'student_system.db\')}"\n    )'
new_line = (
    f'    SQLALCHEMY_DATABASE_URI = os.getenv(\n'
    f'        "DATABASE_URL",\n'
    f'        "mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_ENCODED}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"\n'
    f'    )'
)

if old_line in content:
    content = content.replace(old_line, new_line)
    with open(config_path, "w") as f:
        f.write(content)
    print("  [OK] config.py updated — now pointing to MySQL.")
else:
    # Already updated or format different — just overwrite the URI line
    import re
    content = re.sub(
        r'SQLALCHEMY_DATABASE_URI\s*=\s*os\.getenv\(.*?\)',
        f'SQLALCHEMY_DATABASE_URI = os.getenv(\n        "DATABASE_URL",\n        "mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD_ENCODED}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"\n    )',
        content,
        flags=re.DOTALL
    )
    with open(config_path, "w") as f:
        f.write(content)
    print("  [OK] config.py updated via regex — now pointing to MySQL.")

# ── Update requirements.txt ───────────────────────────────────────────────────
req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "requirements.txt")
with open(req_path, "r") as f:
    req = f.read()
if "PyMySQL" not in req:
    with open(req_path, "a") as f:
        f.write("PyMySQL>=1.1.0\n")
    print("  [OK] requirements.txt updated with PyMySQL.")

print("\n" + "="*60)
print("  [SUCCESS] MIGRATION COMPLETE!")
print(f"  Database : MySQL — {MYSQL_DB}")
print(f"  Host     : {MYSQL_HOST}:{MYSQL_PORT}")
print(f"  User     : {MYSQL_USER}")
print("  Run 'python app.py' to start the server.")
print("="*60 + "\n")
