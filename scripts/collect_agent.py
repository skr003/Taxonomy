#!/usr/bin/env python3
import os
import json
import uuid
import subprocess
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "output")
OUTPUT_FILE = os.path.join(WORKSPACE, "artifacts.json")

# Paths grouped into categories
CATEGORIES = {
    "system_logs": [
        "/var/log/auth.log", "/var/log/secure",
        "/var/log/syslog", "/var/log/messages",
        "/var/log/dmesg", "/var/log/kern.log",
        "/var/log/faillog"
    ],
    "user_activity": [
        "/var/log/lastlog", "/var/run/utmp", "/var/log/wtmp",
        "/var/log/btmp"
    ],
    "network": [
        "/etc/hosts", "/etc/hostname", "/etc/resolv.conf",
        "/proc/net/tcp", "/proc/net/udp"
    ],
    "configuration": [
        "/etc/passwd", "/etc/shadow", "/etc/group", "/etc/sudoers"
    ],
    "applications": [
        "/etc/crontab", "/var/spool/cron/",
        "/etc/systemd/", "/usr/lib/systemd/",
        "/var/log/apt/history.log", "/var/log/yum.log",
        "/etc/apt/sources.list"
    ],
    "processes": [
        "/proc/meminfo", "/proc/cpuinfo"
    ],
    "files": [
        "/lost+found/", "/media/", "/mnt/", "/tmp/", "/var/tmp/"
    ],
    "packages": [
        "/var/lib/dpkg/", "/var/lib/rpm/"
    ],
    "other": [
        "/home/", "/etc/ssh/", "/dev/shm/"
    ]
}

def safe_read(path):
    try:
        # Handle user activity binary files with proper commands
        if path.endswith("wtmp"):
            return subprocess.getoutput("last -f /var/log/wtmp")
        if path.endswith("utmp"):
            return subprocess.getoutput("who")
        if path.endswith("lastlog"):
            return subprocess.getoutput("lastlog")
        if path.endswith("btmp"):
            return subprocess.getoutput("last -f /var/log/btmp")

        # Handle directories
        if os.path.isdir(path):
            return f"[directory listing] {os.listdir(path)}"

        # Handle regular text files
        with open(path, "r", errors="ignore") as f:
            return f.read()

    except Exception as e:
        return f"[unavailable: {e}]"

def collect():
    os.makedirs(WORKSPACE, exist_ok=True)
    artifacts = {
        "case_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    for category, paths in CATEGORIES.items():
        artifacts[category] = []
        for p in paths:
            content = safe_read(p)
            artifacts[category].append({
                "path": p,
                "content": content
            })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(artifacts, f, indent=2)

    print(f"[+] Artifacts collected in {OUTPUT_FILE}")

if __name__ == "__main__":
    collect()
