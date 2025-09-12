#!/usr/bin/env python3
import os
import json
import uuid
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "forensic_workspace")
INPUT_FILE = os.path.join(WORKSPACE, "artifacts.json")
OUTPUT_FILE = os.path.join(WORKSPACE, "formatted_logs.json")

def load_artifacts():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run collect_agent.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

def normalize_items(category, section):
    """
    Convert each log file into multiple items (one per line).
    """
    items = []
    for entry in section:
        path = entry.get("path")
        content = entry.get("content", "")

        if not content:
            continue

        # Split content into individual lines
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            items.append({
                "id": f"{category}-{uuid.uuid4()}",
                "type": category,
                "name": os.path.basename(path) if path else category,
                "path": path,
                "line_number": idx + 1,
                "message": line.strip(),
                "meta": {"source": path}
            })
    return items

if __name__ == "__main__":
    os.makedirs(WORKSPACE, exist_ok=True)
    artifacts = load_artifacts()

    combined_items = []
    for category, section in artifacts.items():
        if category in ["case_id", "timestamp"]:
            continue
        items = normalize_items(category, section)
        combined_items.extend(items)

    with open(OUTPUT_FILE, "w") as f:
        json.dump({
            "case_id": artifacts.get("case_id", "default-case"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": combined_items
        }, f, indent=2)

    print(f"[+] Combined formatted logs written to {OUTPUT_FILE}")
