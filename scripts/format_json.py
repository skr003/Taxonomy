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
    Handles multiple possible formats of artifacts:
    - dict of path: content
    - list of {path, content}
    - nested dict with 'logs'
    """
    items = []
    if isinstance(section, dict):
        # Format 1: {"path": "content", ...}
        for path, content in section.items():
            if isinstance(content, (str, int, float)):
                items.append({
                    "id": f"{category}-{uuid.uuid4()}",
                    "type": category,
                    "name": os.path.basename(path),
                    "path": path,
                    "meta": {"raw": str(content)}
                })
            elif isinstance(content, dict) and "content" in content:
                items.append({
                    "id": f"{category}-{uuid.uuid4()}",
                    "type": category,
                    "name": os.path.basename(content.get("path", path)),
                    "path": content.get("path", path),
                    "meta": {"raw": content.get("content")}
                })

    elif isinstance(section, list):
        # Format 2: [{"path": "...", "content": "..."}, ...]
        for entry in section:
            if isinstance(entry, dict) and "path" in entry and "content" in entry:
                items.append({
                    "id": f"{category}-{uuid.uuid4()}",
                    "type": category,
                    "name": os.path.basename(entry["path"]),
                    "path": entry["path"],
                    "meta": {"raw": entry["content"]}
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
        section = artifacts.get(category, {})
        items = normalize_items(category, section)
        save_category(filename, items)
        combined_items.extend(items)

    # Save one combined file as well
    with open(os.path.join(WORKSPACE, "formatted_logs.json"), "w") as f:
        json.dump({
            "case_id": "default-case",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": combined_items
        }, f, indent=2)
