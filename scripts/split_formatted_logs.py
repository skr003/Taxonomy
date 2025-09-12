#!/usr/bin/env python3
import os
import json
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "forensic_workspace")
INPUT_FILE = os.path.join(WORKSPACE, "formatted_logs.json")

# Map paths/titles to categories
PATH_MAP = {
    # 1. System Logs and Events
    "/var/log/": "system_logs",
    "/var/log/auth.log": "system_logs",
    "/var/log/secure": "system_logs",
    "/var/log/syslog": "system_logs",
    "/var/log/messages": "system_logs",
    "/var/log/dmesg": "system_logs",
    "/var/log/kern.log": "system_logs",
    "/var/log/faillog": "system_logs",

    # 2. User Activity and Commands
    ".bash_history": "user_activity",
    "/var/log/lastlog": "user_activity",
    "/var/run/utmp": "user_activity",
    "/var/log/wtmp": "user_activity",
    "/var/log/btmp": "user_activity",
    "/home/": "user_activity",

    # 3. Network
    "/etc/hosts": "network",
    "/etc/hostname": "network",
    "/etc/resolv.conf": "network",
    "/etc/ssh/": "network",
    "/proc/net/": "network",

    # 4. System & User Config
    "/etc/passwd": "configuration",
    "/etc/shadow": "configuration",
    "/etc/group": "configuration",
    "/etc/sudoers": "configuration",

    # 5. Services / Crontab
    "/etc/crontab": "services",
    "/var/spool/cron/": "services",
    "/etc/systemd/": "services",
    "/usr/lib/systemd/": "services",

    # 6. Processes / Memory
    "/proc/": "processes",
    "/proc/meminfo": "processes",
    "/proc/cpuinfo": "processes",
    "/dev/shm/": "processes",

    # 7. Filesystem & Metadata
    "/lost+found/": "filesystem",
    "/media/": "filesystem",
    "/mnt/": "filesystem",

    # 8. Packages
    "/var/lib/dpkg/": "packages",
    "/var/lib/rpm/": "packages",
    "/etc/apt/sources.list": "packages",
    "/var/log/apt/history.log": "packages",
    "/var/log/yum.log": "packages",

    # 9. Other
    "/tmp": "other",
    "/var/tmp": "other",
    ".ssh": "other",
    ".config": "other",
    ".cache": "other",
    "/etc/fstab": "other",
}

OUTPUT_FILES = {
    "system_logs": "system_logs.json",
    "user_activity": "user_activity.json",
    "network": "network.json",
    "configuration": "configuration.json",
    "services": "services.json",
    "processes": "processes.json",
    "filesystem": "filesystem.json",
    "packages": "packages.json",
    "other": "other.json",
}

def categorize_item(item):
    path = str(item.get("name", "")) + " " + str(item.get("meta", {}).get("path", ""))
    for key, cat in PATH_MAP.items():
        if key in path:
            return cat
    return "other"

def load_formatted_logs():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"{INPUT_FILE} not found. Run format_json.py first.")
    with open(INPUT_FILE, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    os.makedirs(WORKSPACE, exist_ok=True)
    data = load_formatted_logs()

    categorized = {cat: [] for cat in OUTPUT_FILES}

    for item in data.get("items", []):
        cat = categorize_item(item)
        categorized[cat].append(item)

    # Write per-category JSON
    for cat, filename in OUTPUT_FILES.items():
        outfile = os.path.join(WORKSPACE, filename)
        with open(outfile, "w") as f:
            json.dump({
                "case_id": data.get("case_id", "default-case"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "items": categorized[cat]
            }, f, indent=2)
        print(f"[+] Wrote {len(categorized[cat])} items to {outfile}")
