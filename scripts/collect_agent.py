#!/usr/bin/env python3
"""
Forensic Collection Agent
Collects system logs, user activity, network info, configuration, processes, and more.
Adds fallback messages with timestamps when no evidence is found.
"""

import argparse, json, os, subprocess, pwd, time, re

parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True, help="Output JSON file")
args = parser.parse_args()

timestamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

artifacts = {
    "timestamp": timestamp,
    "system_logs": {},
    "user_activity": {},
    "network": {},
    "config": {},
    "processes": {},
    "filesystem": {},
    "packages": {},
    "other": {}
}

def safe_read(path, binary=False):
    """Read a file safely as text or binary hex"""
    try:
        mode = "rb" if binary else "r"
        with open(path, mode) as f:
            return f.read() if not binary else f.read().hex()
    except Exception:
        return None

def run_cmd(cmd):
    """Run a shell command and capture output"""
    try:
        out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)
        return out.strip()
    except subprocess.CalledProcessError:
        return None

def add_message(category, key, message):
    """Add a fallback message with timestamp"""
    artifacts[category][key] = {
        "message": f"{message} at {timestamp}"
    }

# --------------------------
# 1. System Logs & Events
# --------------------------
log_paths = [
    "/var/log/auth.log", "/var/log/secure",
    "/var/log/syslog", "/var/log/messages",
    "/var/log/dmesg", "/var/log/kern.log",
    "/var/log/faillog"
]
for lp in log_paths:
    content = safe_read(lp, binary=lp.endswith("faillog"))
    if content:
        artifacts["system_logs"][lp] = content
    else:
        add_message("system_logs", lp, "No log data available")

# --------------------------
# 2. User Activity & Commands
# --------------------------
artifacts["user_activity"]["bash_history"] = {}
for u in pwd.getpwall():
    hist_file = os.path.join(u.pw_dir, ".bash_history")
    content = safe_read(hist_file)
    if content:
        artifacts["user_activity"]["bash_history"][u.pw_name] = content
    else:
        artifacts["user_activity"]["bash_history"][u.pw_name] = f"No history found at {timestamp}"

special_logs = ["/var/log/lastlog", "/var/run/utmp", "/var/log/wtmp", "/var/log/btmp"]
for sp in special_logs:
    content = safe_read(sp, binary=True)
    if content:
        artifacts["user_activity"][sp] = content
    else:
        add_message("user_activity", sp, "No user activity recorded")

if os.path.exists("/home"):
    artifacts["user_activity"]["home_dirs"] = os.listdir("/home")
else:
    artifacts["user_activity"]["home_dirs"] = f"No /home directory found at {timestamp}"

# --------------------------
# 3. Network Connections & Config
# --------------------------
net_files = ["/etc/hosts", "/etc/hostname", "/etc/resolv.conf"]
for nf in net_files:
    content = safe_read(nf)
    if content:
        artifacts["network"][nf] = content
    else:
        add_message("network", nf, "No network config found")

if os.path.exists("/etc/ssh"):
    artifacts["network"]["/etc/ssh"] = os.listdir("/etc/ssh")
else:
    artifacts["network"]["/etc/ssh"] = f"No SSH config directory found at {timestamp}"

for f in ["tcp", "udp"]:
    path = f"/proc/net/{f}"
    content = safe_read(path)
    if content:
        artifacts["network"].setdefault("proc_net", {})[f] = content
    else:
        add_message("network", f"/proc/net/{f}", "No data found")

netstat = run_cmd("ss -tulpn || netstat -tulpn")
if netstat:
    artifacts["network"]["netstat"] = netstat
else:
    add_message("network", "netstat", "No active network connections found")

# --------------------------
# 4. System & User Config
# --------------------------
for cfg in ["/etc/passwd", "/etc/shadow", "/etc/group", "/etc/sudoers"]:
    content = safe_read(cfg)
    if content:
        artifacts["config"][cfg] = content
    else:
        add_message("config", cfg, "File not accessible or missing")

# --------------------------
# 5. Application & Service Config
# --------------------------
for svc in ["/etc/crontab", "/var/spool/cron", "/etc/systemd", "/usr/lib/systemd"]:
    if os.path.isdir(svc):
        artifacts["config"][svc] = os.listdir(svc)
    elif os.path.isfile(svc):
        artifacts["config"][svc] = safe_read(svc)
    else:
        add_message("config", svc, "Not present on system")

# --------------------------
# 6. Processes & Memory
# --------------------------
ps_output = run_cmd("ps aux")
artifacts["processes"]["ps_aux"] = ps_output or f"No running processes captured at {timestamp}"
artifacts["processes"]["proc_meminfo"] = safe_read("/proc/meminfo") or f"No memory info at {timestamp}"
artifacts["processes"]["proc_cpuinfo"] = safe_read("/proc/cpuinfo") or f"No CPU info at {timestamp}"
artifacts["processes"]["dev_shm"] = os.listdir("/dev/shm") if os.path.exists("/dev/shm") else f"No /dev/shm at {timestamp}"

# --------------------------
# 7. Files & Directories Metadata
# --------------------------
for p in ["/lost+found", "/media", "/mnt"]:
    if os.path.exists(p):
        artifacts["filesystem"][p] = os.listdir(p)
    else:
        add_message("filesystem", p, "Directory not found")

# --------------------------
# 8. Package Management & Installed Software
# --------------------------
dpkg_list = run_cmd("dpkg -l") if os.path.exists("/var/lib/dpkg") else None
rpm_list = run_cmd("rpm -qa") if os.path.exists("/var/lib/rpm") else None
artifacts["packages"]["dpkg_list"] = dpkg_list or f"No dpkg data at {timestamp}"
artifacts["packages"]["rpm_list"] = rpm_list or f"No rpm data at {timestamp}"
artifacts["packages"]["sources_list"] = safe_read("/etc/apt/sources.list") or f"No sources.list at {timestamp}"
artifacts["packages"]["apt_history"] = safe_read("/var/log/apt/history.log") or f"No apt history at {timestamp}"
artifacts["packages"]["yum_history"] = safe_read("/var/log/yum.log") or f"No yum history at {timestamp}"

# --------------------------
# 9. Other Evidence Paths
# --------------------------
for tmpdir in ["/tmp", "/var/tmp"]:
    if os.path.exists(tmpdir):
        artifacts["other"][tmpdir] = os.listdir(tmpdir)
    else:
        add_message("other", tmpdir, "Directory not found")

# --------------------------
# Explicit: Failed Login Attempts
# --------------------------
faillog_output = run_cmd("faillog -a")
lastb_output = run_cmd("lastb -n 20")

if faillog_output:
    artifacts["system_logs"]["failed_logins"] = {"faillog": faillog_output}
else:
    artifacts["system_logs"]["failed_logins"] = {"message": f"No failed login attempts since {timestamp}"}

if lastb_output:
    artifacts["system_logs"]["failed_logins"]["lastb"] = lastb_output
else:
    artifacts["system_logs"]["failed_logins"]["lastb"] = f"No failed login attempts since {timestamp}"



import re

failed_attempts = []
try:
    with open("/var/log/auth.log", "r") as f:
        for line in f:
            if "Failed password" in line or "Invalid user" in line:
                parts = line.split()
                timestamp = " ".join(parts[0:3])
                user = None
                ip = None
                # crude parse
                if "from" in parts:
                    idx = parts.index("from")
                    ip = parts[idx+1]
                if "user" in parts:
                    idx = parts.index("user")
                    user = parts[idx+1]

                failed_attempts.append({
                    "timestamp": timestamp,
                    "username": user,
                    "source_ip": ip,
                    "status": "Failed",
                    "message": line.strip()
                })
except FileNotFoundError:
    failed_attempts.append({
        "timestamp": None,
        "username": None,
        "source_ip": None,
        "status": "Info",
        "message": "No auth.log file found"
    })

artifacts["failed_ssh"] = failed_attempts




# --------------------------
# Save everything
# --------------------------
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "w") as f:
    json.dump(artifacts, f, indent=2)

print(f"[+] Forensic collection completed. Artifacts saved to {args.out}")
