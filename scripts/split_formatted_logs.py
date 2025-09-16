#!/usr/bin/env python3
import os
import json
from datetime import datetime

INPUT_FILE = "output/formatted_logs.json"
OUTPUT_DIR = "output/split_logs"

CATEGORY_FILES = {
    "system_logs_and_events": "system_logs.json",
    "user_activity_and_commands": "user_activity.json",
    "network_connections_and_configuration": "network.json",
    "system_and_user_configuration": "config.json",
    "application_and_service_configurations": "applications.json",
    "processes_and_memory": "processes.json",
    "files_and_directories_metadata": "filesystem.json",
    "package_management_and_installed_software": "packages.json",
    "other_potential_evidence_paths": "others.json",
}

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} not found. Run format_json.py first.")
        return

    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

    # Initialize buckets
    categorized = {k: [] for k in CATEGORY_FILES}

    for category in categorized:
        # Only include if present in data
        if category in data:
            categorized[category] = data.get(category, [])

    # Write out each file
    for section, filename in CATEGORY_FILES.items():
        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w") as f:
            json.dump(
                {
                    "category": section,
                    "timestamp": timestamp,
                    "count": len(categorized[section]),
                    "items": categorized[section],
                },
                f,
                indent=2,
            )
        print(f"[INFO] Written {out_path} with {len(categorized[section])} entries")

if __name__ == "__main__":
    main()
