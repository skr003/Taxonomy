#!/usr/bin/env python3
"""
Forensic agent: collects live system data and evidence files.
Outputs a single JSON file (--out).
"""

import argparse, json, os, time, platform, getpass, subprocess, base64, uuid

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True, help="Output artifact JSON path")
args = parser.parse_args()

def safe_read_file(path, binary=False, limit=20000):
    """Read a file safely (truncate and base64 if binary)."""
    try:
        mode = "rb" if binary else "r"
        with open(path, mode) as f:
            data = f.read(limit)
        if binary:
            return base64.b64encode(data).decode("utf-8")
        else:
            return data
    except Exception as e:
        return f"ERROR: {e}"

def run_cmd(cmd, limit=20000):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return p.stdout[:limit]
    except Exception as e:
        return f"ERROR: {e}"

artifacts = {
    "case_id": str(uuid.uuid4()),
    "host": platform.node(),
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "user": getpass.getuser(),
    "os": platform.platform(),
    "logs": {},
    "user_activity": {},
    "network": {},
    "config": {},
    "processes": {},
    "filesystem": {},
    "packages": {},
    "temp_files": {},
}

# 1. System Logs
log_files = [
    "/var/log/auth.log", "/var/log/secure", "/var/log/syslog",
    "/var/log/messages", "/var/log/dmesg", "/var/log/kern.log", "/var/log/faillog"
]
for lf in log_files:
    artifacts["logs"][lf] = safe_read_file(lf)

# 2. User Activity
user_activity_files = [
    "/var/log/lastlog", "/var/run/utmp", "/var/log/wtmp",
    "/var/log/btmp"
]
for uf in user_activity_files:
    artifacts["user_activity"][uf] = safe_read_file(uf, binary=True)

# Bash history per user
try:
    for u in os.listdir("/home"):
        hist_path = os.path.join("/home", u, ".bash_history")
        if os.path.exists(hist_path):
            artifacts["user_activity"][f"{u}_bash_history"] = safe_read_file(hist_path)
except Exception as e:
    artifacts["user_activity"]["error"] = str(e)

# 3. Network
artifacts["network"]["/etc/hosts"] = safe_read_file("/etc/hosts")
artifacts["network"]["/etc/hostname"] = safe_read_file("/etc/hostname")
artifacts["network"]["/etc/resolv.conf"] = safe_read_file("/etc/resolv.conf")
artifacts["network"]["/etc/ssh"] = run_cmd(["ls", "-la", "/etc/ssh"])
artifacts["network"]["/proc/net/tcp"] = safe_read_file("/proc/net/tcp")
artifacts["network"]["/proc/net/udp"] = safe_read_file("/proc/net/udp")

# 4. System/User Config
config_files = ["/etc/passwd", "/etc/shadow", "/etc/group", "/etc/sudoers"]
for cf in config_files:
    artifacts["config"][cf] = safe_read_file(cf)

# 5. Application/Service Configs
artifacts["config"]["/etc/crontab"] = safe_read_file("/etc/crontab")
artifacts["config"]["/var/spool/cron"] = run_cmd(["ls", "-la", "/var/spool/cron"])
artifacts["config"]["systemd_units"] = run_cmd(["systemctl", "list-units", "--no-pager"])

# 6. Processes and Memory
artifacts["processes"]["ps_aux"] = run_cmd(["ps", "aux"])
artifacts["processes"]["/proc/meminfo"] = safe_read_file("/proc/meminfo")
artifacts["processes"]["/proc/cpuinfo"] = safe_read_file("/proc/cpuinfo")

# 7. Filesystem
fs_paths = ["/lost+found", "/media", "/mnt"]
for p in fs_paths:
    artifacts["filesystem"][p] = run_cmd(["ls", "-la", p])
artifacts["filesystem"]["/etc/fstab"] = safe_read_file("/etc/fstab")

# 8. Packages
if os.path.exists("/var/lib/dpkg"):
    artifacts["packages"]["dpkg_list"] = run_cmd(["dpkg", "-l"])
    artifacts["packages"]["sources_list"] = safe_read_file("/etc/apt/sources.list")
    artifacts["packages"]["history_log"] = safe_read_file("/var/log/apt/history.log")
elif os.path.exists("/var/lib/rpm"):
    artifacts["packages"]["rpm_list"] = run_cmd(["rpm", "-qa"])
    artifacts["packages"]["yum_log"] = safe_read_file("/var/log/yum.log")

# 9. Temp files
artifacts["temp_files"]["/tmp"] = run_cmd(["ls", "-la", "/tmp"])
artifacts["temp_files"]["/var/tmp"] = run_cmd(["ls", "-la", "/var/tmp"])
artifacts["temp_files"]["/dev/shm"] = run_cmd(["ls", "-la", "/dev/shm"])

# Save
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "w") as f:
    json.dump(artifacts, f, indent=2)

print(f"Wrote artifacts to {args.out} with case_id {artifacts['case_id']}")
