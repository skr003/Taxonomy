#!/usr/bin/env python3
"""
Store prioritized artifact metadata into SQLite database.
"""

import argparse, json, sqlite3, os

parser = argparse.ArgumentParser()
parser.add_argument("--db", required=True, help="SQLite DB path")
parser.add_argument("--meta", required=True, help="Prioritized JSON file")
args = parser.parse_args()

os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)

# Load prioritized list safely
with open(args.meta) as f:
    data = json.load(f)

prioritized = data.get("prioritized") or []

conn = sqlite3.connect(args.db)
cur = conn.cursor()

# Create table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS prioritized (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    pid INTEGER,
    name TEXT,
    laddr TEXT,
    raddr TEXT,
    status TEXT,
    reason TEXT,
    score INTEGER
)
""")

# Insert each record
for a in prioritized:
    cur.execute("""
    INSERT INTO prioritized(type, pid, name, laddr, raddr, status, reason, score)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        a.get("type"),
        a.get("pid"),
        a.get("name"),
        a.get("laddr"),
        a.get("raddr"),
        a.get("status"),
        a.get("reason"),
        a.get("score")
    ))

conn.commit()
conn.close()

print(f"Stored {len(prioritized)} prioritized records in {args.db}")
