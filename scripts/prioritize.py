#!/usr/bin/env python3
"""
Prioritize artifacts based on simple heuristics.
Handles both structured (psutil) and raw text process lists.
"""

import argparse, json, os

parser = argparse.ArgumentParser()
parser.add_argument("--in", dest="input", required=True, help="Input artifact JSON file")
parser.add_argument("--out", required=True, help="Output priority JSON file")
args = parser.parse_args()

with open(args.input) as f:
    data = json.load(f)

prioritized = []

# Heuristic 1: processes with suspicious names
suspicious_names = ["nc", "netcat", "socat", "nmap", "bash", "sh"]

processes = data.get("processes", {})

# Case A: structured list (from psutil)
if isinstance(processes, list):
    for proc in processes:
        if isinstance(proc, dict):
            name = proc.get("name", "").lower()
            if any(s in name for s in suspicious_names):
                prioritized.append({
                    "type": "process",
                    "pid": proc.get("pid"),
                    "name": proc.get("name"),
                    "reason": "Suspicious process name",
                    "score": 9
                })

# Case B: dict containing raw ps_aux output
elif isinstance(processes, dict):
    ps_aux = processes.get("ps_aux")
    if ps_aux:
        if isinstance(ps_aux, str):
            lines = ps_aux.splitlines()
        elif isinstance(ps_aux, list):
            lines = ps_aux
        else:
            lines = []

        for line in lines:
            if any(s in line.lower() for s in suspicious_names):
                prioritized.append({
                    "type": "process",
                    "name": line.strip(),
                    "reason": "Suspicious process in ps output",
                    "score": 8
                })

# Heuristic 2: network connections with remote addresses
connections = data.get("connections") or data.get("network", {}).get("net_stat")
if isinstance(connections, list):
    for conn in connections:
        if isinstance(conn, dict) and conn.get("raddr"):
            prioritized.append({
                "type": "connection",
                "pid": conn.get("pid"),
                "laddr": conn.get("laddr"),
                "raddr": conn.get("raddr"),
                "status": conn.get("status"),
                "reason": "Active remote connection",
                "score": 7
            })
elif isinstance(connections, str):
    for line in connections.splitlines():
        if "ESTABLISHED" in line or "LISTEN" in line:
            prioritized.append({
                "type": "connection",
                "name": line.strip(),
                "reason": "Suspicious active connection",
                "score": 6
            })

# Always write out valid JSON
out = {"prioritized": prioritized or []}
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "w") as f:
    json.dump(out, f, indent=2)

print(f"Wrote priority list to {args.out}, {len(prioritized)} items")
