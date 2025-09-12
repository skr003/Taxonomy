#!/usr/bin/env python3
"""
mitre_attack.py

Read partitioned forensic JSON files (default: forensic_workspace/separated/)
and produce a single compact JSON mapping of observed artifacts -> MITRE techniques.

Output (default): forensic_workspace/mitre_mapping.json

Output schema (compact, no 'name' fields):
{
  "case_id": "<case_id or default-case>",
  "generated_at": "<ISO timestamp>",
  "total_items_scanned": <int>,
  "by_technique": {
    "T1078": {
      "tactic": "Credential Access",
      "count": 12,
      "samples": [
         {"id":"system_logs-abc","source_file":"system_logs.json"},
         ...
      ]
    },
    ...
  },
  "by_tactic": {
    "Credential Access": {"count": 20, "techniques": {"T1078":12, "T1003":8}}
  },
  "unmapped_count": 5,
  "unmapped_samples": [
    {"id":"log-xyz","source_file":"system_logs.json"}, ...
  ]
}
"""

import os
import json
from datetime import datetime
from collections import defaultdict, Counter

# Configuration (override with env vars if needed)
SEPARATED_DIR = os.environ.get("SEPARATED_DIR", "forensic_workspace/separated")
OUTPUT_FILE = os.environ.get("MITRE_OUTPUT", "forensic_workspace/mitre_mapping.json")
SAMPLE_LIMIT = int(os.environ.get("SAMPLE_LIMIT", "5"))

# Simple keyword -> technique mapping. Extend as needed.
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
    "/tmp": ["T1070","T1564","T1105"],
    "var/tmp": ["T1070","T1564","T1105"],
    "dev/shm": ["T1070","T1564","T1105"],
    "dpkg": ["T1105","T1059"],
    "apt": ["T1105"],
    "yum": ["T1105"],
    ".ssh": ["T1021","T1564"],
    "ps aux": ["T1059","T1057"],
    "meminfo": ["T1055"],
}

# Map technique -> friendly tactic (used only in output)
TECH_ID_TO_TACTIC = {
    "T1078": "Credential Access",
    "T1110": "Credential Access",
    "T1098": "Credential Access",
    "T1003": "Credential Access",
    "T1059": "Execution",
    "T1053": "Persistence",
    "T1543.002": "Persistence",
    "T1037": "Persistence",
    "T1021": "Lateral Movement",
    "T1090": "Command and Control",
    "T1049": "Discovery",
    "T1071": "Command and Control",
    "T1070": "Defense Evasion",
    "T1564": "Defense Evasion",
    "T1105": "Execution",
    "T1057": "Discovery",
    "T1055": "Defense Evasion",
}

def load_all_items(directory):
    """Load all items from JSON files in directory. Returns list of tuples (source_fname, item_dict)."""
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Separated directory not found: {directory}")

    records = []
    for fname in sorted(os.listdir(directory)):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, "r") as fh:
                j = json.load(fh)
                items = j.get("items", [])
                # ensure items is iterable
                if isinstance(items, list):
                    for it in items:
                        # minimal expected fields: id, type, name
                        records.append((fname, it))
        except Exception as e:
            # skip bad files but warn
            print(f"[WARN] could not read {path}: {e}")
    return records

def match_techniques(item):
    """
    Determine technique IDs by simple substring matching against item fields.
    Uses item['name'] and item['type'] and item['id'] if present.
    """
    hits = set()
    combined = " ".join([
        str(item.get("id","")),
        str(item.get("type","")),
        str(item.get("name",""))
    ]).lower()
    for key, techs in KEYWORD_TO_TECH.items():
        if key in combined:
            hits.update(techs)
    return hits

def technique_tactic(tid):
    return TECH_ID_TO_TACTIC.get(tid, "Unknown")

def build_mitre_mapping(records):
    tech_counter = Counter()
    tactic_counter = Counter()
    samples = defaultdict(list)
    unmapped = []

    for src_file, item in records:
        techs = match_techniques(item)
        if not techs:
            # keep a small sample of unmapped items (id + source_file)
            if len(unmapped) < SAMPLE_LIMIT:
                unmapped.append({
                    "id": item.get("id"),
                    "source_file": src_file
                })
            continue

        for t in sorted(techs):
            tech_counter[t] += 1
            tactic_counter[technique_tactic(t)] += 1
            if len(samples[t]) < SAMPLE_LIMIT:
                samples[t].append({
                    "id": item.get("id"),
                    "source_file": src_file
                })

    # Build by_technique dict minimal structure (no 'name' fields)
    by_tech = {}
    for t, cnt in tech_counter.items():
        by_tech[t] = {
            "tactic": technique_tactic(t),
            "count": cnt,
            "samples": samples.get(t, [])
        }

    # Build by_tactic summary with technique counts
    by_tactic = {}
    for t, meta in by_tech.items():
        tac = meta["tactic"]
        if tac not in by_tactic:
            by_tactic[tac] = {"count": 0, "techniques": {}}
        by_tactic[tac]["count"] += meta["count"]
        by_tactic[tac]["techniques"][t] = meta["count"]

    return by_tech, by_tactic, len(records), unmapped

def extract_case_id_from_files(directory):
    # Try to read case_id from any file that includes it
    try:
        for fname in sorted(os.listdir(directory)):
            if not fname.lower().endswith(".json"):
                continue
            path = os.path.join(directory, fname)
            with open(path, "r") as fh:
                j = json.load(fh)
                cid = j.get("case_id") or j.get("case")
                if cid:
                    return cid
    except Exception:
        pass
    return "default-case"

def main():
    records = load_all_items(SEPARATED_DIR)
    total = len(records)
    print(f"[INFO] Loaded {total} items from {SEPARATED_DIR}")

    by_tech, by_tactic, scanned, unmapped_samples = build_mitre_mapping(records)

    output = {
        "case_id": extract_case_id_from_files(SEPARATED_DIR),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_items_scanned": scanned,
        "by_technique": by_tech,
        "by_tactic": by_tactic,
        "unmapped_count": len(records) - sum(v["count"] for v in by_tech.values()) if by_tech else len(records),
        "unmapped_samples": unmapped_samples
    }

    # ensure output dir exists
    os.makedirs(os.path.dirname(OUTPUT_FILE) or ".", exist_ok=True)
    with open(OUTPUT_FILE, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"[INFO] MITRE mapping written to {OUTPUT_FILE}")
    print(f"[INFO] techniques: {len(by_tech)}, tactics: {len(by_tactic)}, unmapped: {output['unmapped_count']}")

if __name__ == "__main__":
    main()
