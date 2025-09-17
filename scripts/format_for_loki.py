#!/usr/bin/env python3
import json
import argparse
from datetime import datetime

def load_priority_file(path):
    with open(path, "r") as f:
        return json.load(f)

def to_loki_payload(priority_data):
    streams = []
    for artifact in priority_data.get("artifacts", []):
        timestamp = str(int(datetime.utcnow().timestamp() * 1e9))  # ns precision
        line = json.dumps(artifact)
        streams.append({
            "stream": {"job": "forensic_logs", "component": artifact.get("component", "unknown")},
            "values": [[timestamp, line]]
        })
    return {"streams": streams}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", dest="output", required=True)
    args = parser.parse_args()

    data = load_priority_file(args.input)
    payload = to_loki_payload(data)

    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[+] Loki payload saved to {args.output}")
