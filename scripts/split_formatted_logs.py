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

# Map old collector categories → new taxonomy keys
CATEGORY_MAP = {
    "system_logs": "system_logs_and_events",
    "user_activity": "user_activity_and_commands",
    "network": "network_connections_and_configuration",
    "configuration": "system_and_user_configuration",
    "applications": "application_and_service_configurations",
    "processes": "processes_and_memory",
    "files": "files_and_directories_metadata",
    "packages": "package_management_and_installed_software",
    "other": "other_potential_evidence_paths",
}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} not found. Run format_json.py first.")
        return

    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    items = data.get("items", [])
    timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

    categorized = {key: [] for key in CATEGORY_FILES}

    # Distribute items into mapped categories
    for item in items:
        old_cat = item.get("type", "other")
        new_cat = CATEGORY_MAP.get(old_cat, "other_potential_evidence_paths")
        categorized[new_cat].append(item)

    # Write each category file
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
