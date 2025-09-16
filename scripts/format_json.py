#!/usr/bin/env python3
import json
import os
from datetime import datetime

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
        return json.load(f)

def format_artifacts(artifacts):
    formatted = {
        "case_id": artifacts.get("case_id", "unknown"),
        "timestamp": artifacts.get("timestamp", datetime.utcnow().isoformat() + "Z"),
    }

    # Keep categories as top-level keys with items
    for section, data in artifacts.items():
        if section in ("case_id", "timestamp"):
            continue
        if isinstance(data, list):
            formatted[section] = data
        else:
            formatted[section] = [data]
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
