#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Base forensic directory
WORKSPACE_DIR = os.getcwd()
FORENSIC_DIR = os.path.join(WORKSPACE_DIR, "output")
INPUT_FILE = os.path.join(FORENSIC_DIR, "artifacts.json")
OUTPUT_FILE = os.path.join(FORENSIC_DIR, "formatted_logs.json")

def load_artifacts():
    print(f"[INFO] Looking for input file at: {INPUT_FILE}")
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} not found. Did collect_agent.py run successfully?")
        return None
    with open(INPUT_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            return None

def format_artifacts(artifacts):
    formatted = {
        "case_id": artifacts.get("case_id", "unknown"),
        "timestamp": artifacts.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "items": []
    }

    for section, data in artifacts.items():
        if section in ("case_id", "timestamp"):
            continue
        if isinstance(data, dict):
            for key, value in data.items():
                formatted["items"].append({
                    "id": f"{section}-{key}",
                    "type": section,
                    "name": str(key),
                    "meta": value if isinstance(value, (dict, list)) else {"raw": str(value)}
                })
        elif isinstance(data, list):
            for i, entry in enumerate(data):
                formatted["items"].append({
                    "id": f"{section}-{i}",
                    "type": section,
                    "name": str(entry.get("name", entry)) if isinstance(entry, dict) else str(entry),
                    "meta": entry if isinstance(entry, dict) else {"raw": str(entry)}
                })
        else:
            formatted["items"].append({
                "id": f"{section}-single",
                "type": section,
                "name": section,
                "meta": {"raw": str(data)}
            })
    return formatted

def save_formatted(formatted):
    print(f"[INFO] Writing output to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(formatted, f, indent=2)

if __name__ == "__main__":
    artifacts = load_artifacts()
    if not artifacts:
        exit(1)
    formatted = format_artifacts(artifacts)
    save_formatted(formatted)
    print("[INFO] Done: formatted_logs.json created successfully")
