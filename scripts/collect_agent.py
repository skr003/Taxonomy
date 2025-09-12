#!/usr/bin/env python3
import os
import json
from datetime import datetime

timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# Helper: read file contents safely (NO TRIMMING)
def read_file(path):
    if not os.path.exists(path):
        return f"[Not Found] {path}"
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read()
    except PermissionError:
        return f"[Permission Denied] {path}"
    except Exception as e:
        return f"[Error: {str(e)}]"

# Helper: list directory contents safely
def list_dir(path):
    if not os.path.exists(path):
        return f"[Not Found] {path}"
    try:
        return os.listdir(path)
    except PermissionError:
        return f"[Permission Denied] {path}"
    except Exception as e:
        return f"[Error: {str(e)}]"

# Helper: add entry to logs
def add_log(section, title, path, content):
    artifacts["logs"].append({
        "section": section,
        "title": title,
        "path": path,
        "content": content
    })

# Initialize artifact dictionary
artifacts = {
    "case_id": os.environ.get("CASE_ID", "default-case"),
    "timestamp": timestamp,
    "logs": []
}

# ===============================
# 1. System Logs and Events
# ===============================
system_logs = [
    ("/var/log/auth.log", "Authentication Log"),
    ("/var/log/secure", "Authentication Log (RHEL/CentOS)"),
    ("/var/log/syslog", "System Log"),
    ("/var/log/messages", "Messages Log"),
    ("/var/log/dmesg", "Kernel Boot/Hardware Messages"),
    ("/var/log/kern.log", "Kernel Log"),
    ("/var/log/faillog", "Failed Login Attempts")
]
for path, title in system_logs:
    add_log("System Logs and Events", title, path, read_file(path))

# ===============================
# 2. User Activity and Commands
# ===============================
user_activity = [
    ("/var/log/lastlog", "Last Login Records"),
    ("/var/run/utmp", "Currently Logged-in Users"),
    ("/var/log/wtmp", "Login/Logout Records"),
    ("/var/log/btmp", "Failed Login Attempts Log")
]
for path, title in user_activity:
    add_log("User Activity and Commands", title, path, read_file(path))

# Per-user bash history + home listing
for user in os.listdir("/home"):
    hist_path = f"/home/{user}/.bash_history"
    add_log("User Activity and Commands", f"{user} Bash History", hist_path, read_file(hist_path))
    add_log("User Activity and Commands", f"{user} Home Directory", f"/home/{user}", list_dir(f"/home/{user}"))

# ===============================
# 3. Network Connections and Config
# ===============================
network_conf = [
    ("/etc/hosts", "Hosts File"),
    ("/etc/hostname", "System Hostname"),
    ("/etc/resolv.conf", "DNS Resolver Config"),
    ("/etc/ssh", "SSH Config Directory")
]
for path, title in network_conf:
    if os.path.isdir(path):
        add_log("Network Connections and Configuration", title, path, list_dir(path))
    else:
        add_log("Network Connections and Configuration", title, path, read_file(path))

add_log("Network Connections and Configuration", "Active TCP Connections", "/proc/net/tcp", read_file("/proc/net/tcp"))
add_log("Network Connections and Configuration", "Active UDP Connections", "/proc/net/udp", read_file("/proc/net/udp"))

# ===============================
# 4. System and User Configuration
# ===============================
sys_user_conf = [
    ("/etc/passwd", "User Accounts"),
    ("/etc/shadow", "Password Hashes"),
    ("/etc/group", "User Groups"),
    ("/etc/sudoers", "Sudo Permissions")
]
for path, title in sys_user_conf:
    add_log("System and User Configuration", title, path, read_file(path))

# ===============================
# 5. Application and Service Configurations
# ===============================
app_conf = [
    ("/etc/crontab", "System Cron Jobs"),
    ("/var/spool/cron", "User Cron Jobs"),
    ("/etc/systemd", "Systemd Services (etc)"),
    ("/usr/lib/systemd", "Systemd Services (usr/lib)")
]
for path, title in app_conf:
    if os.path.isdir(path):
        add_log("Application and Service Configurations", title, path, list_dir(path))
    else:
        add_log("Application and Service Configurations", title, path, read_file(path))

# ===============================
# 6. Processes and Memory
# ===============================
proc_mem = [
    ("/proc/meminfo", "Memory Info"),
    ("/proc/cpuinfo", "CPU Info"),
    ("/dev/shm", "Shared Memory")
]
for path, title in proc_mem:
    if os.path.isdir(path):
        add_log("Processes and Memory", title, path, list_dir(path))
    else:
        add_log("Processes and Memory", title, path, read_file(path))

# Full process list
add_log("Processes and Memory", "Process List", "ps aux", os.popen("ps aux").read())

# ===============================
# 7. Files and Directories Metadata
# ===============================
fs_meta = [
    ("/lost+found", "Recovered Files"),
    ("/media", "Mounted Media"),
    ("/mnt", "Mounted Filesystems"),
    ("/home", "User Home Directories")
]
for path, title in fs_meta:
    add_log("Files and Directories Metadata", title, path, list_dir(path))

# ===============================
# 8. Package Management and Installed Software
# ===============================
pkg_mgmt = [
    ("/var/lib/dpkg", "DPKG Database (Debian)"),
    ("/var/lib/rpm", "RPM Database (RedHat)"),
    ("/etc/apt/sources.list", "APT Repositories"),
    ("/var/log/apt/history.log", "APT Package History"),
    ("/var/log/yum.log", "YUM Package History")
]
for path, title in pkg_mgmt:
    if os.path.isdir(path):
        add_log("Package Management and Installed Software", title, path, list_dir(path))
    else:
        add_log("Package Management and Installed Software", title, path, read_file(path))

# ===============================
# 9. Other Potential Evidence Paths
# ===============================
tmp_dirs = ["/tmp", "/var/tmp"]
for path in tmp_dirs:
    add_log("Other Potential Evidence", "Temporary Directory", path, list_dir(path))

# Hidden dirs/files inside /home
for user in os.listdir("/home"):
    user_home = f"/home/{user}"
    try:
        hidden = [d for d in os.listdir(user_home) if d.startswith(".")]
        add_log("Other Potential Evidence", f"{user} Hidden Dirs", user_home, hidden)
    except Exception as e:
        add_log("Other Potential Evidence", f"{user} Hidden Dirs", user_home, str(e))

# Mounted filesystems from /etc/fstab
add_log("Other Potential Evidence", "Filesystem Mounts", "/etc/fstab", read_file("/etc/fstab"))

# ===============================
# Write JSON Output
# ===============================
out_file = "/tmp/artifacts.json"
with open(out_file, "w") as f:
    json.dump(artifacts, f, indent=2)

print(f"[INFO] Forensic collection complete. Output: {out_file}")
