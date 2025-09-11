#!/usr/bin/env python3
"""
Format raw artifacts.json into normalized JSON for dashboards.
Handles both structured psutil dicts and raw text outputs.
"""

import argparse, json, time, uuid

parser = argparse.ArgumentParser()
parser.add_argument("--in", dest="input", required=True, help="Input artifact JSON")
parser.add_argument("--out", required=True, help="Formatted JSON output")
args = parser.parse_args()

with open(args.input) as f:
    data = json.load(f)

formatted = {
    "case_id": str(uuid.uuid4()),
    "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    "items": []
}

# ---- Processes ----
processes = data.get("processes", [])
if isinstance(processes, list):
    for p in processes:
        if isinstance(p, dict):
            formatted['items'].append({
                "id": f"proc-{p.get('pid','')}",
                "type": "process",
                "name": p.get("name"),
                "username": p.get("username"),
                "meta": p
            })
        elif isinstance(p, str):
            formatted['items'].append({
                "id": f"proc-line-{hash(p)}",
                "type": "process",
                "name": p.strip(),
                "username": None,
                "meta": {"raw": p.strip()}
            })
elif isinstance(processes, dict):
    ps_aux = processes.get("ps_aux")
    if ps_aux:
        lines = ps_aux.splitlines() if isinstance(ps_aux, str) else ps_aux
        for line in lines:
            formatted['items'].append({
                "id": f"proc-line-{hash(line)}",
                "type": "process",
                "name": line.strip(),
                "username": None,
                "meta": {"raw": line.strip()}
            })

# ---- Connections ----
connections = data.get("connections") or data.get("network", {}).get("net_stat")
if isinstance(connections, list):
    for c in connections:
        if isinstance(c, dict):
            formatted['items'].append({
                "id": f"conn-{c.get('pid','')}-{c.get('laddr')}",
                "type": "connection",
                "laddr": c.get("laddr"),
                "raddr": c.get("raddr"),
                "status": c.get("status"),
                "meta": c
            })
        elif isinstance(c, str):
            formatted['items'].append({
                "id": f"conn-line-{hash(c)}",
                "type": "connection",
                "meta": {"raw": c.strip()}
            })
elif isinstance(connections, str):
    for line in connections.splitlines():
        formatted['items'].append({
            "id": f"conn-line-{hash(line)}",
            "type": "connection",
            "meta": {"raw": line.strip()}
        })

# ---- Fallback ----
if not formatted["items"]:
    formatted["items"].append({
        "id": "no-data",
        "type": "info",
        "message": "No forensic artifacts were collected",
        "meta": {}
    })

with open(args.out, "w") as f:
    json.dump(formatted, f, indent=2)

print(f"Formatted {len(formatted['items'])} items into {args.out}")
