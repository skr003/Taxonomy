#!/usr/bin/env python3
"""
Prioritize artifacts based on simple heuristics.
Takes a JSON artifact dump and outputs a priority list.
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

for proc in data.get("processes", []):
    name = proc.get("name", "").lower()
    if any(s in name for s in suspicious_names):
        prioritized.append({
            "type": "process",
            "pid": proc.get("pid"),
            "name": proc.get("name"),
            "reason": "Suspicious process name",
            "score": 9
        })

# Heuristic 2: network connections with foreign addresses
for conn in data.get("connections", []):
    if conn.get("raddr"):
        prioritized.append({
            "type": "connection",
            "pid": conn.get("pid"),
            "laddr": conn.get("laddr"),
            "raddr": conn.get("raddr"),
            "status": conn.get("status"),
            "reason": "Active remote connection",
            "score": 7
        })

# Always write out valid JSON structure
out = {
    "prioritized": prioritized or []
}

os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "w") as f:
    json.dump(out, f, indent=2)

print(f"Wrote priority list to {args.out}, {len(prioritized)} items")
