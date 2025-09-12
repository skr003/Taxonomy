#!/usr/bin/env python3
import json
import os
from datetime import datetime

INPUT_FILE = "forensic_workspace/artifacts.json"
OUTPUT_DIR = "forensic_workspace"

CATEGORY_FILES = {
    "system_logs": "system_logs.json",
    "user_activity": "user_activity.json",
    "network": "network.json",
    "system_config": "system_config.json",
    "application_config": "application_config.json",
    "processes_memory": "processes_memory.json",
    "files_metadata": "files_metadata.json",
    "packages": "packages.json",
    "other_evidence": "other_evidence.json"
}

def load_artifacts():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run collect_agent.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

def save_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

def main():
    artifacts = load_artifacts()
    timestamp = datetime.utcnow().isoformat() + "Z"

    # create directory if missing
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for category, filename in CATEGORY_FILES.items():
        items = artifacts.get(category, {})

        # Normalize into list of dicts
        formatted_items = []
        if isinstance(items, dict):
            for key, val in items.items():
                formatted_items.append({
                    "id": f"{category}-{key}",
                    "type": "logs",
                    "section": category,
                    "title": key,
                    "path": key,
                    "content": val if isinstance(val, str) else json.dumps(val)
                })
        elif isinstance(items, list):
            for idx, val in enumerate(items):
                formatted_items.append({
                    "id": f"{category}-{idx}",
                    "type": "logs",
                    "section": category,
                    "title": category,
                    "path": category,
                    "content": val if isinstance(val, str) else json.dumps(val)
                })

        data = {
            "case_id": artifacts.get("case_id", "default-case"),
            "timestamp": timestamp,
            "items": formatted_items
        }

        save_json(data, os.path.join(OUTPUT_DIR, filename))

    print(f"[INFO] Split artifacts.json into {len(CATEGORY_FILES)} files under {OUTPUT_DIR}")

if __name__ == "__main__":
    INPUT_FILE = os.path.join(WORKSPACE_DIR, "artifacts.json")
    OUTPUT_DIR = FORENSIC_DIR

    artifacts = load_artifacts(INPUT_FILE)
    timestamp = datetime.utcnow().isoformat() + "Z"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Write category-based JSON files
    for category, entries in artifacts.items():
        if category in CATEGORY_FILES:
            save_json(
                {
                    "case_id": artifacts.get("case_id", "default-case"),
                    "timestamp": timestamp,
                    "items": entries,
                },
                os.path.join(OUTPUT_DIR, CATEGORY_FILES[category]),
            )

    # ✅ Also write combined file for mindmap_export.py
    combined = {
        "case_id": artifacts.get("case_id", "default-case"),
        "timestamp": timestamp,
        "items": []
    }
    for category, filename in CATEGORY_FILES.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
                combined["items"].extend(data.get("items", []))

    save_json(combined, os.path.join(OUTPUT_DIR, "formatted_logs.json"))
    print("[INFO] Wrote combined forensic_workspace/formatted_logs.json for compatibility")
