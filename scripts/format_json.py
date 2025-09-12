#!/usr/bin/env python3
import json
import os
from datetime import datetime

# Use workspace-relative paths
INPUT_FILE = "artifacts.json"
OUTPUT_FILE = "formatted_logs.json"

def load_artifacts():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run collect_agent.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

def format_artifacts(artifacts):
    formatted = {
        "case_id": artifacts.get("case_id", "unknown"),
        "timestamp": artifacts.get("timestamp", datetime.utcnow().isoformat() + "Z"),
        "items": []
    }

    # Flatten each section into readable items
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
    with open(OUTPUT_FILE, "w") as f:
        json.dump(formatted, f, indent=2)

if __name__ == "__main__":
    artifacts = load_artifacts()
    formatted = format_artifacts(artifacts)
    save_formatted(formatted)
    print(f"Formatted logs saved to {OUTPUT_FILE}")
