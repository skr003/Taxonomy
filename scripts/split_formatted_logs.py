# scripts/process_logs.py
import os
import json
import hashlib
from datetime import datetime

INPUT_FILE = "output/formatted_logs.json"
ALL_LOGS_FILE = "output/artifacts.json"
OUTPUT_DIR = "output/separated"

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

    # Step 1: Load formatted_logs.json
    with open(INPUT_FILE, "r") as f:
        data = json.load(f)

    items = data.get("items", [])
    timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

    cleaned_items = []

    # Step 2: Clean items (remove meta, keep id/type/name)
    for idx, item in enumerate(items):
        try:
            meta = {}
            try:
                meta = eval(item.get("name", "{}"))
            except Exception:
                continue

            raw_line = str(meta.get("content", ""))
            line_id = hashlib.md5(raw_line.encode()).hexdigest()[:12]

            cleaned_items.append({
                "id": f"log-{line_id}",
                "type": meta.get("section", "other_potential_evidence_paths").replace(" ", "_").lower(),
                "name": f"[{meta.get('title', 'Unknown')}] ({meta.get('path', 'N/A')}): {raw_line}"
            })
        except Exception as e:
            cleaned_items.append({
                "id": f"error-{idx}",
                "type": "error",
                "name": f"[Parsing Error] {str(e)}"
            })

    # Step 3: Save all_logs.json
    all_logs = {
        "case_id": data.get("case_id", "default-case"),
        "timestamp": timestamp,
        "items": cleaned_items
    }

    with open(ALL_LOGS_FILE, "w") as f:
        json.dump(all_logs, f, indent=2)

    print(f"Created {ALL_LOGS_FILE} with {len(cleaned_items)} items")

    # Step 4: Partition into 9 files
    categorized = {key: [] for key in CATEGORY_FILES}

    for item in cleaned_items:
        section = item.get("type", "other_potential_evidence_paths")
        if section not in CATEGORY_FILES:
            section = "other_potential_evidence_paths"
        categorized[section].append(item)

    for section, filename in CATEGORY_FILES.items():
        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "items": categorized[section]
            }, f, indent=2)
        print(f"Written {out_path} with {len(categorized[section])} entries")


if __name__ == "__main__":
    main()
