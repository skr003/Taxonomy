#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from hashlib import sha256

# --- Taxonomy Scoring ---
# Higher = more volatile & evidentiary
CATEGORY_SCORES = {
    "processes": 10,       # volatile
    "network": 9,          # volatile
    "system_logs": 8,      # semi-volatile
    "user_activity": 7,
    "applications": 6,
    "configuration": 5,    # persistent
    "files": 4,
    "packages": 3,
    "other": 1
}

EVIDENCE_BOOST = {
    "failed password": 5,
    "error": 3,
    "denied": 3,
    "ssh": 2,
    "root": 2
}


def compute_hash(obj) -> str:
    """Stable SHA256 hash of artifact entry"""
    return sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def score_artifact(category, content):
    """Base score from category + boosts from content"""
    score = CATEGORY_SCORES.get(category, 1)
    content_lower = content.lower()

    for keyword, boost in EVIDENCE_BOOST.items():
        if keyword in content_lower:
            score += boost
    return score


def prioritize(data):
    prioritized = []

    for category, artifacts in data.items():
        if category in ("case_id", "timestamp"):
            continue
        for entry in artifacts:
            content = entry.get("content", "")
            score = score_artifact(category, content)
            prioritized.append({
                "category": category,
                "path": entry.get("path"),
                "score": score,
                "reason": f"{category} artifact",
                "hash": compute_hash(entry)
            })

    prioritized.sort(key=lambda x: x["score"], reverse=True)
    return prioritized


def main():
    parser = argparse.ArgumentParser(description="Prioritize forensic artifacts")
    parser.add_argument("--in", dest="input_file", required=True, help="Input output/artifacts.json")
    parser.add_argument("--out", dest="output_file", required=True, help="Output output/priority_list.json")
    args = parser.parse_args()

    with open(args.input_file, "r") as f:
        data = json.load(f)

    prioritized = prioritize(data)

    output = {
        "case_id": data.get("case_id"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_artifacts": len(prioritized),
        "priority_list": prioritized
    }

    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    with open(args.output_file, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[+] Prioritization complete → {args.output_file}")


if __name__ == "__main__":
    main()
