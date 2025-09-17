#!/usr/bin/env python3
import argparse
import json
import os
import sys

def load_priority_file(path):
    with open(path, "r") as f:
        return json.load(f)

def to_loki_payload(data):
    # Convert priority.json data into Loki push format
    streams = []
    for artifact in data.get("artifacts", []):
        stream = {
            "stream": {
                "component": artifact.get("component", "unknown"),
                "path": artifact.get("path", ""),
                "priority": str(artifact.get("priority", ""))
            },
            "values": [
                [str(int(artifact.get("timestamp", 0) * 1e9)), json.dumps(artifact)]
            ]
        }
        streams.append(stream)
    return {"streams": streams}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, help="/var/lib/jenkins/workspace/Taxonomy_NEW/output/priority_list.json")
    parser.add_argument("--out", dest="output", required=True, help="/var/lib/jenkins/workspace/Taxonomy_NEW/output/loki_payload.json")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[!] Input file not found: {args.input}")
        sys.exit(1)

    data = load_priority_file(args.input)
    payload = to_loki_payload(data)

    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[+] Loki payload written to {args.output}")
