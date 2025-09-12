#!/usr/bin/env python3
import json
import os
from datetime import datetime

INPUT_FILE = "/tmp/artifacts.json"
OUTPUT_FILE = "/tmp/formatted_logs.json"

def load_artifacts():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run collect_agent.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

def format_logs(artifacts):
    case_id = artifacts.get("case_id", "unknown-case")
    timestamp = artifacts.get("timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
    logs = artifacts.get("logs", [])

    formatted = {
        "case_id": case_id,
        "timestamp": timestamp,
        "sections": {}
    }

    # Organize by section → each section is a table-like list
    for log in logs:
        section = log.get("section", "Uncategorized")
        entry = {
            "title": log.get("title", ""),
            "path": log.get("path", ""),
            "content": log.get("content", "")
        }

        if section not in formatted["sections"]:
            formatted["sections"][section] = []

        formatted["sections"][section].append(entry)

    return formatted

def save_formatted(data):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Formatted logs written to {OUTPUT_FILE}")

if __name__ == "__main__":
    artifacts = load_artifacts()
    formatted = format_logs(artifacts)
    save_formatted(formatted)
