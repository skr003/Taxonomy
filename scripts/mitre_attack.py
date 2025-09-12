#!/usr/bin/env python3
"""
mitre_attack.py (clean version)

Produces forensic_workspace/mitre_mapping.json
with minimal fields (no meta).
"""

import os
import json
from datetime import datetime
from collections import defaultdict, Counter

SEPARATED_DIR = os.environ.get("SEPARATED_DIR", "forensic_workspace/separated")
OUTPUT_FILE = os.environ.get("MITRE_OUTPUT", "forensic_workspace/mitre_mapping.json")
SAMPLE_LIMIT = 5

KEYWORD_TO_TECH = {
    "auth.log": ["T1078","T1110","T1098"],
    "failed password": ["T1110"],
    "invalid user": ["T1110","T1078"],
    "btmp": ["T1110"],
    "faillog": ["T1110"],
    "lastlog": ["T1078"],
    "wtmp": ["T1078"],
    "passwd": ["T1078","T1098"],
    "shadow": ["T1003"],
    ".bash_history": ["T1059"],
    "bash_history": ["T1059"],
    "crontab": ["T1053"],
    "cron": ["T1053"],
    "systemd": ["T1543.002","T1037"],
    "/etc/systemd": ["T1543.002"],
    "ssh": ["T1021","T1090"],
    "/etc/ssh": ["T1021","T1090"],
    "proc/net": ["T1049"],
    "/proc/net": ["T1049"],
    "tcp": ["T1049","T1071"],
    "udp": ["T1049","T1071"],
    "tmp": ["T1070","T1564","T1105"],
    "/tmp": ["T1070","T1564","T1105"],
    "var/tmp": ["T1070","T1564","T1105"],
    "dev/shm": ["T1070","T1564","T1105"],
    "dpkg": ["T1105","T1059"],
    "apt": ["T1105"],
    "yum": ["T1105"],
    "ssh authorized_keys": ["T1021"],
    ".ssh": ["T1021","T1564"],
    "ps aux": ["T1059","T1057"],
    "meminfo": ["T1055"],
}

TECH_ID_TO_META = {
    "T1078": {"name": "Valid Accounts", "tactic": "Credential Access"},
    "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
    "T1098": {"name": "Account Manipulation", "tactic": "Credential Access"},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access"},
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "Persistence"},
    "T1543.002": {"name": "Create or Modify Systemd Service", "tactic": "Persistence"},
    "T1037": {"name": "Boot or Logon Initialization Scripts", "tactic": "Persistence"},
    "T1021": {"name": "Remote Services", "tactic": "Lateral Movement"},
    "T1090": {"name": "Proxy", "tactic": "Command and Control"},
    "T1049": {"name": "System Network Connections Discovery", "tactic": "Discovery"},
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
    "T1070": {"name": "Indicator Removal on Host", "tactic": "Defense Evasion"},
    "T1564": {"name": "Hide Artifacts", "tactic": "Defense Evasion"},
    "T1105": {"name": "Ingress Tool Transfer", "tactic": "Execution"},
    "T1057": {"name": "Process Discovery", "tactic": "Discovery"},
    "T1055": {"name": "Process Injection", "tactic": "Defense Evasion"},
}

def load_all(directory):
    records = []
    for fname in os.listdir(directory):
        if fname.endswith(".json"):
            with open(os.path.join(directory, fname)) as f:
                j = json.load(f)
                for it in j.get("items", []):
                    records.append((fname, it))
    return records

def match(item):
    combined = (item.get("name","") + " " + item.get("type","")).lower()
    hits = set()
    for key, techs in KEYWORD_TO_TECH.items():
        if key in combined:
            hits.update(techs)
    return hits

def main():
    records = load_all(SEPARATED_DIR)

    by_tech = {}
    by_tactic = {}
    unmapped = []

    tech_counts = Counter()
    tactic_counts = Counter()
    samples = defaultdict(list)

    for src, item in records:
        techs = match(item)
        if not techs:
            if len(unmapped) < SAMPLE_LIMIT:
                unmapped.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "source_file": src
                })
            continue
        for t in techs:
            meta = TECH_ID_TO_META.get(t, {"name":"Unknown","tactic":"Unknown"})
            tech_counts[t] += 1
            tactic_counts[meta["tactic"]] += 1
            if len(samples[t]) < SAMPLE_LIMIT:
                samples[t].append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "source_file": src
                })

    for t, count in tech_counts.items():
        meta = TECH_ID_TO_META.get(t, {"name":"Unknown","tactic":"Unknown"})
        by_tech[t] = {
            "name": meta["name"],
            "tactic": meta["tactic"],
            "count": count,
            "samples": samples[t]
        }

    for tactic, count in tactic_counts.items():
        by_tactic[tactic] = {"count": count}

    output = {
        "case_id": "default-case",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_items_scanned": len(records),
        "by_technique": by_tech,
        "by_tactic": by_tactic,
        "unmapped_count": len(records) - sum(tech_counts.values()),
        "unmapped_samples": unmapped
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[INFO] Wrote clean MITRE mapping to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
