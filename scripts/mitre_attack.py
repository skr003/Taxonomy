#!/usr/bin/env python3
"""
mitre_auth.py

Maps Authentication & User Accounts artifacts (user_accounts.json)
to MITRE ATT&CK techniques.

Output: forensic_workspace/mitre_auth.json
"""

import os
import json
from datetime import datetime
from collections import defaultdict, Counter

INPUT_FILE = os.environ.get("USER_ACCOUNTS_FILE", "forensic_workspace/separated/user_accounts.json")
OUTPUT_FILE = os.environ.get("MITRE_AUTH_OUTPUT", "forensic_workspace/mitre_auth.json")
SAMPLE_LIMIT = 5

# Keywords to MITRE Technique mapping
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
}

TECH_ID_TO_META = {
    "T1078": {"name": "Valid Accounts", "tactic": "Credential Access"},
    "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
    "T1098": {"name": "Account Manipulation", "tactic": "Credential Access"},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access"},
}

def load_items(path):
    if not os.path.exists(path):
        print(f"[WARN] Input file not found: {path}")
        return []
    with open(path) as f:
        j = json.load(f)
        return j.get("items", [])

def match(item):
    combined = (item.get("name","") + " " + item.get("type","")).lower()
    hits = set()
    for key, techs in KEYWORD_TO_TECH.items():
        if key in combined:
            hits.update(techs)
    return hits

def main():
    items = load_items(INPUT_FILE)

    by_tech = {}
    by_tactic = {}
    unmapped = []

    tech_counts = Counter()
    tactic_counts = Counter()
    samples = defaultdict(list)

    for item in items:
        techs = match(item)
        if not techs:
            if len(unmapped) < SAMPLE_LIMIT:
                unmapped.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "source_file": "user_accounts.json"
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
                    "source_file": "user_accounts.json"
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
        "total_items_scanned": len(items),
        "by_technique": by_tech,
        "by_tactic": by_tactic,
        "unmapped_count": len(items) - sum(tech_counts.values()),
        "unmapped_samples": unmapped
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[INFO] MITRE auth mapping saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
