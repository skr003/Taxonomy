#!/usr/bin/env python3
import os
import json
import uuid
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "forensic_workspace")
INPUT_FILE = os.path.join(WORKSPACE, "artifacts.json")

CATEGORY_FILES = {
    "system_logs": "system_logs.json",
    "user_activity": "user_activity.json",
    "network": "network.json",
    "configuration": "configuration.json",
    "applications": "applications.json",
    "processes": "processes.json",
    "files": "files.json",
    "packages": "packages.json",
    "other": "other.json"
}

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

        # Split log file into lines
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

def save_category(filename, items):
    outpath = os.path.join(WORKSPACE, filename)
    with open(outpath, "w") as f:
        json.dump({
            "case_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": items
        }, f, indent=2)

if __name__ == "__main__":
    os.makedirs(WORKSPACE, exist_ok=True)
    artifacts = load_artifacts()

    combined_items = []
    for category, filename in CATEGORY_FILES.items():
        section = artifacts.get(category, [])
        items = normalize_items(category, section)
        save_category(filename, items)
        combined_items.extend(items)

    # Save combined file
    with open(os.path.join(WORKSPACE, "formatted_logs.json"), "w") as f:
        json.dump({
            "case_id": artifacts.get("case_id", "default-case"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": combined_items
        }, f, indent=2)

    print(f"[+] Formatted logs written to {WORKSPACE}")
