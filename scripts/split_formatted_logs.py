#!/usr/bin/env python3
import os
import json
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "forensic_workspace")
INPUT_FILE = os.path.join(WORKSPACE, "formatted_logs.json")

# 9 output categories (based on your earlier list)
CATEGORIES = {
    "system_logs": "system_logs.json",
    "user_activity": "user_activity.json",
    "network": "network.json",
    "configuration": "configuration.json",
    "services": "services.json",
    "processes": "processes.json",
    "filesystem": "filesystem.json",
    "packages": "packages.json",
    "other": "other.json"
}

def load_formatted_logs():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run format_json.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    os.makedirs(WORKSPACE, exist_ok=True)
    data = load_formatted_logs()

    # Prepare category buckets
    categorized = {cat: [] for cat in CATEGORIES}

    for item in data.get("items", []):
        t = item.get("type", "other")
        if t in categorized:
            categorized[t].append(item)
        else:
            categorized["other"].append(item)

    # Write out per-category JSONs
    for cat, filename in CATEGORIES.items():
        outfile = os.path.join(WORKSPACE, filename)
        with open(outfile, "w") as f:
            json.dump({
                "case_id": data.get("case_id", "default-case"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "items": categorized[cat]
            }, f, indent=2)
        print(f"[+] Wrote {len(categorized[cat])} items to {outfile}")
