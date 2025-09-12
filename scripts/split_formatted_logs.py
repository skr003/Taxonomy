import os
import json
import hashlib
from datetime import datetime

INPUT_FILE = "forensic_workspace/formatted_logs.json"
OUTPUT_DIR = "forensic_workspace/separated"

CATEGORY_FILES = {
    "System Logs and Events": ("system_logs.json", "system_logs"),
    "User Activity and Commands": ("user_activity.json", "user_activity"),
    "Network Connections and Configuration": ("network.json", "network"),
    "System and User Configuration": ("config.json", "config"),
    "Application and Service Configurations": ("applications.json", "applications"),
    "Processes and Memory": ("processes.json", "processes"),
    "Files and Directories Metadata": ("filesystem.json", "filesystem"),
    "Package Management and Installed Software": ("packages.json", "packages"),
    "Other Potential Evidence Paths": ("others.json", "others"),
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

items = data.get("items", [])
timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

categorized = {cat: [] for cat in CATEGORY_FILES}

for idx, item in enumerate(items):
    try:
        # forcefully parse string to dict, ignore meta
        meta = {}
        try:
            meta = eval(item.get("name", "{}"))
        except Exception:
            continue  # skip if it’s not valid

        section = meta.get("section", "Other Potential Evidence Paths")
        out_file, log_type = CATEGORY_FILES.get(section, ("others.json", "others"))

        raw_line = str(meta.get("content", ""))
        line_id = hashlib.md5(raw_line.encode()).hexdigest()[:12]

        entry = {
            "id": f"{log_type}-{line_id}",
            "type": log_type,
            "name": f"[{meta.get('title', 'Unknown')}] ({meta.get('path', 'N/A')}): {raw_line}"
        }

        categorized[section].append(entry)

    except Exception as e:
        categorized["Other Potential Evidence Paths"].append({
            "id": f"error-{idx}",
            "type": "error",
            "name": f"[Parsing Error] {str(e)}"
        })

# Write outputs
for section, (filename, _) in CATEGORY_FILES.items():
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w") as f:
        json.dump(categorized[section], f, indent=2)
    print(f"Written {out_path} with {len(categorized[section])} entries")
