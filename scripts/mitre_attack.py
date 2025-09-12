#!/usr/bin/env python3
"""
mitre_attack.py

Read the partitioned forensic JSON files (default: forensic_workspace/separated/)
and produce a single JSON mapping of observed artifacts -> MITRE techniques & tactics.

Output: forensic_workspace/mitre_mapping.json

Format (example):
{
  "case_id": "default-case",
  "timestamp": "2025-09-12T11:00:00Z",
  "by_technique": {
    "T1078": {
      "name": "Valid Accounts",
      "tactic": "Credential Access",
      "count": 12,
      "samples": [
         {"id":"system_logs-abc","name":"[Authentication Log] ...","source_file":"system_logs.json"},
         ...
      ]
    },
    ...
  },
  "by_tactic": {
    "Credential Access": {"count": 20, "techniques": {"T1078":12, "T1003":8}},
    ...
  },
  "unmapped_count": 5
}
"""
import os
import json
from datetime import datetime
from collections import defaultdict, Counter

# Config: where your partitioned files live and the output path
SEPARATED_DIR = os.environ.get("SEPARATED_DIR", "forensic_workspace/separated")
OUTPUT_FILE = os.environ.get("MITRE_OUTPUT", "forensic_workspace/mitre_mapping.json")
SAMPLE_LIMIT = 5   # number of example items to retain per technique

# A keyword -> techniques mapping (lowercase keys). Extend as needed.
KEYWORD_TO_TECH = {
    # Authentication & accounts
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
    "proc/net": ["T1049"],  # network discovery
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
    "ps aux": ["T1059","T1057"],  # process discovery
    "meminfo": ["T1055"],  # memory-related (T1055 is Process Injection - rough)
    "cpuinfo": [],
    # add more keywords -> technique mappings as needed
}

# Map known technique IDs to human-friendly technique name and tactic.
# Keep this mapping limited to the techniques we may use above.
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
    # default fallback if technique unknown: tactic "Unknown"
}

def load_all_files(directory):
    """Load JSON files from directory. Expect each file to be JSON with 'items' list."""
    records = []   # tuple(source_file, item_dict)
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Separated directory not found: {directory}")
    for fname in sorted(os.listdir(directory)):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        try:
            with open(path, "r") as fh:
                j = json.load(fh)
                items = j.get("items", [])
                for it in items:
                    records.append( (fname, it) )
        except Exception as e:
            # skip malformed files but note them as unmapped later
            print(f"[WARN] Skipping {path}: {e}")
    return records

def match_techniques(item):
    """Given an item (dict with id,type,name), return a set of technique IDs."""
    techniques = set()
    name = str(item.get("name","")).lower()
    # Try to inspect both name and type for keywords
    combined = (name + " " + str(item.get("type","")).lower())
    for key, techs in KEYWORD_TO_TECH.items():
        if key in combined:
            techniques.update(techs)
    return techniques

def technique_id_to_meta(tid):
    meta = TECH_ID_TO_META.get(tid)
    if meta:
        return meta["name"], meta["tactic"]
    else:
        return "Unknown Technique", "Unknown"

def build_mapping(records):
    by_tech = {}
    tactic_counter = Counter()
    technique_counter = Counter()
    unmapped = []

    # store sample entries for each technique
    samples = defaultdict(list)

    for source_file, item in records:
        techs = match_techniques(item)
        if not techs:
            unmapped.append( {"source_file": source_file, "id": item.get("id"), "name": item.get("name")} )
            continue

        for t in techs:
            technique_counter[t] += 1
            name, tactic = technique_id_to_meta(t)
            tactic_counter[tactic] += 1
            if len(samples[t]) < SAMPLE_LIMIT:
                samples[t].append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "source_file": source_file
                })

    # Build by_technique structure
    for t, count in technique_counter.items():
        name, tactic = technique_id_to_meta(t)
        by_tech[t] = {
            "technique_id": t,
            "name": name,
            "tactic": tactic,
            "count": count,
            "samples": samples.get(t, [])
        }

    # Build by_tactic summary
    by_tactic = {}
    for t, meta in by_tech.items():
        tactic = meta["tactic"]
        if tactic not in by_tactic:
            by_tactic[tactic] = {"count": 0, "techniques": {}}
        by_tactic[tactic]["count"] += meta["count"]
        by_tactic[tactic]["techniques"][t] = meta["count"]

    return {
        "by_technique": by_tech,
        "by_tactic": by_tactic,
        "unmapped_count": len(unmapped),
        "unmapped_samples": unmapped[:SAMPLE_LIMIT]
    }

def main():
    records = load_all_files(SEPARATED_DIR)
    print(f"[INFO] Loaded {len(records)} items from {SEPARATED_DIR}")

    mapping = build_mapping(records)

    output = {
        "case_id": None,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_items_scanned": len(records),
        "by_technique": mapping["by_technique"],
        "by_tactic": mapping["by_tactic"],
        "unmapped_count": mapping["unmapped_count"],
        "unmapped_samples": mapping["unmapped_samples"]
    }

    # try to grab case_id from any file if present
    try:
        # load first file's case_id if available
        any_file = next((f for f in os.listdir(SEPARATED_DIR) if f.lower().endswith(".json")), None)
        if any_file:
            with open(os.path.join(SEPARATED_DIR, any_file), "r") as fh:
                j = json.load(fh)
                if "case_id" in j:
                    output["case_id"] = j.get("case_id")
    except Exception:
        pass

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as fh:
        json.dump(output, fh, indent=2)

    print(f"[INFO] Wrote MITRE mapping to {OUTPUT_FILE}")
    print(f"[INFO] Techniques found: {len(output['by_technique'])}, tactics: {len(output['by_tactic'])}, unmapped: {output['unmapped_count']}")

if __name__ == "__main__":
    main()
