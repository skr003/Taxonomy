import os
import json
from datetime import datetime

INPUT_FILE = "forensic_workspace/formatted_logs.json"
OUTPUT_DIR = "forensic_workspace/separated"

# Mapping of file categories → output filename
CATEGORY_FILES = {
    "System Logs and Events": "system_logs.json",
    "User Activity and Commands": "user_activity.json",
    "Network Connections and Configuration": "network.json",
    "System and User Configuration": "config.json",
    "Application and Service Configurations": "applications.json",
    "Processes and Memory": "processes.json",
    "Files and Directories Metadata": "filesystem.json",
    "Package Management and Installed Software": "packages.json",
    "Other Potential Evidence Paths": "others.json",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

items = data.get("items", [])
timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

# Prepare category buckets
categorized = {cat: [] for cat in CATEGORY_FILES}

for item in items:
    try:
        meta = eval(item.get("name", "{}"))  # stringified dict → dict
        section = meta.get("section", "Other Potential Evidence Paths")
        out_file = CATEGORY_FILES.get(section, "others.json")

        entry = {
            "section": meta.get("section"),
            "title": meta.get("title"),
            "path": meta.get("path"),
            "timestamp": timestamp,
            "line": meta.get("content")
        }
        categorized[section].append(entry)
    except Exception as e:
        categorized["Other Potential Evidence Paths"].append({
            "section": "Parsing Error",
            "title": "Unknown",
            "path": "N/A",
            "timestamp": timestamp,
            "line": f"Error: {str(e)} | Raw: {item}"
        })

# Write out separate files
for section, filename in CATEGORY_FILES.items():
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w") as f:
        json.dump(categorized[section], f, indent=2)
    print(f"Written {out_path} with {len(categorized[section])} entries")
