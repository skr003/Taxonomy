#!/usr/bin/env python3
import os
import json
import uuid
import hashlib
import pwd
import grp
from datetime import datetime

WORKSPACE = os.path.join(os.getcwd(), "output")
OUTPUT_FILE = os.path.join(WORKSPACE, "artifacts.json")

# Mapping each individual path to its explanation
PATH_EXPLANATIONS = {
    # --- System Logs and Events ---
    "/var/log/": "Contains system logs that track different system events.",
    "/var/log/auth.log": "Authentication logs, including user logins and authentication events.",
    "/var/log/secure": "Authentication logs on RHEL/CentOS systems.",
    "/var/log/syslog": "General system log containing messages from kernel and system services.",
    "/var/log/messages": "Non-authentication system messages, useful for tracking general behavior.",
    "/var/log/dmesg": "Kernel log messages (boot, hardware, driver info).",
    "/var/log/kern.log": "Kernel-specific logs for hardware events and errors.",
    "/var/log/faillog": "Records failed login attempts.",

    # --- User Activity and Commands ---
    "~/.bash_history": "Stores command history for users (each user has their own).",
    "/var/log/lastlog": "Records last login times for each user.",
    "/var/run/utmp": "Tracks currently logged-in users.",
    "/var/log/wtmp": "Stores login/logout records, viewable with `last`.",
    "/var/log/btmp": "Logs failed login attempts, viewable with `lastb`.",
    "/home/": "Each user's home directory, with personal files and hidden configs (e.g., .ssh, .config).",

    # --- Network Connections and Configuration ---
    "/etc/hosts": "Local hostname and IP address mappings.",
    "/etc/hostname": "System hostname.",
    "/etc/resolv.conf": "DNS resolver configuration.",
    "/etc/ssh/": "SSH configuration, authorized keys, host keys.",
    "/proc/net/": "Active network connections and network stack info.",
    "/proc/net/tcp": "Active TCP connections.",
    "/proc/net/udp": "Active UDP connections.",

    # --- System and User Configuration ---
    "/etc/passwd": "User account information (usernames, UIDs, shells).",
    "/etc/shadow": "Password hashes for users (root-only access).",
    "/etc/group": "User groups and group memberships.",
    "/etc/sudoers": "Controls sudo/root privileges.",

    # --- Applications and Service Configurations ---
    "/etc/crontab": "System-wide cron job definitions.",
    "/var/spool/cron/": "User-specific cron jobs.",
    "/etc/systemd/": "Systemd service definitions.",
    "/usr/lib/systemd/": "Additional systemd service definitions.",
    "/var/log/apt/history.log": "Debian-based package installation/removal history.",
    "/var/log/yum.log": "RPM-based package installation/removal history.",
    "/etc/apt/sources.list": "Repository sources for Debian-based systems.",

    # --- Processes and Memory ---
    "/proc/": "Virtual filesystem with process and system runtime information.",
    "/proc/meminfo": "Memory usage details.",
    "/proc/cpuinfo": "CPU information.",
    "/dev/shm/": "Shared memory space, sometimes used by malware.",

    # --- Files and Directories Metadata ---
    "/lost+found/": "Recovered files after corruption or fsck runs.",
    "/media/": "Mount points for removable media (USB, CD).",
    "/mnt/": "Mount points for temporary filesystems.",
    "/tmp/": "Temporary files (can contain evidence of activity).",
    "/var/tmp/": "Temporary files that persist between reboots.",

    # --- Package Management ---
    "/var/lib/dpkg/": "Database of installed packages (Debian-based).",
    "/var/lib/rpm/": "Database of installed packages (RPM-based).",

    # --- Other ---
    "/dev/shm/": "Shared memory, potential evidence of in-memory malware."
}

CATEGORIES = {
    "system_logs": [
        "/var/log/auth.log", "/var/log/secure", "/var/log/syslog",
        "/var/log/messages", "/var/log/dmesg", "/var/log/kern.log",
        "/var/log/faillog", "/var/log/"
    ],
    "user_activity": [
        "~/.bash_history", "/var/log/lastlog", "/var/run/utmp",
        "/var/log/wtmp", "/var/log/btmp", "/home/"
    ],
    "network": [
        "/etc/hosts", "/etc/hostname", "/etc/resolv.conf",
        "/etc/ssh/", "/proc/net/", "/proc/net/tcp", "/proc/net/udp"
    ],
    "configuration": [
        "/etc/passwd", "/etc/shadow", "/etc/group", "/etc/sudoers"
    ],
    "applications": [
        "/etc/crontab", "/var/spool/cron/", "/etc/systemd/", "/usr/lib/systemd/",
        "/var/log/apt/history.log", "/var/log/yum.log", "/etc/apt/sources.list"
    ],
    "processes": [
        "/proc/", "/proc/meminfo", "/proc/cpuinfo", "/dev/shm/"
    ],
    "files": [
        "/lost+found/", "/media/", "/mnt/", "/tmp/", "/var/tmp/"
    ],
    "packages": [
        "/var/lib/dpkg/", "/var/lib/rpm/"
    ],
    "other": [
        "/dev/shm/"
    ]
}


def safe_read(path):
    """Read file contents if possible"""
    try:
        if os.path.isdir(path):
            return f"[directory listing] {os.listdir(path)}", True
        with open(path, "r", errors="ignore") as f:
            return f.read(), True
    except Exception as e:
        return f"[unavailable: {e}]", False


def get_metadata(path):
    """Return file metadata and SHA256 hash"""
    try:
        st = os.stat(path)
        metadata = {
            "size": st.st_size,
            "owner": pwd.getpwuid(st.st_uid).pw_name,
            "group": grp.getgrgid(st.st_gid).gr_name,
            "permissions": oct(st.st_mode & 0o777),
            "atime": st.st_atime,
            "mtime": st.st_mtime,
            "ctime": st.st_ctime,
        }
        sha256_hash = None
        if os.path.isfile(path):
            sha256 = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            sha256_hash = sha256.hexdigest()
        metadata["sha256"] = sha256_hash
        return metadata
    except Exception as e:
        return {"error": str(e)}


def collect():
    os.makedirs(WORKSPACE, exist_ok=True)
    artifacts = {
        "case_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    for category, paths in CATEGORIES.items():
        artifacts[category] = []
        for p in paths:
            content, ok = safe_read(p)
            metadata = get_metadata(p)
            explanation = PATH_EXPLANATIONS.get(p, f"No explanation available for {p}")
            status = "collected" if ok else "not_collected"
            artifacts[category].append({
                "path": p,
                "content": content,
                "metadata": metadata,
                "explanation": explanation,
                "tag": category,
                "status": status
            })

    with open(OUTPUT_FILE, "w") as f:
        json.dump(artifacts, f, indent=2)

    print(f"[+] Artifacts collected in {OUTPUT_FILE}")


if __name__ == "__main__":
    collect()
