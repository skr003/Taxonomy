#!/usr/bin/env python3
import argparse
import json
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser(description="Convert split log JSON into Loki payload")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    parser.add_argument("--out", dest="output", required=True, help="Output Loki payload file")
    return parser.parse_args()

def to_nanos(ts: str) -> str:
    """Convert ISO8601 timestamp string to nanoseconds"""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return str(int(dt.timestamp() * 1e9))

def convert_to_loki(data):
    streams = []
    timestamp = to_nanos(data.get("timestamp"))

    for item in data.get("items", []):
        # Loki labels
        labels = {
            "category": data.get("category", "unknown"),
            "id": item.get("id", "no-id"),
            "type": item.get("type", "na"),
            "tag": item.get("meta", {}).get("tag", "na"),
            "status": item.get("meta", {}).get("status", "na"),
        }

        # The actual log line (store full item JSON)
        log_line = json.dumps(item, ensure_ascii=False)

        streams.append({
            "stream": labels,
            "values": [[timestamp, log_line]]
        })

    return {"streams": streams}

def main():
    args = parse_args()

    with open(args.input, "r") as f:
        data = json.load(f)

    payload = convert_to_loki(data)

    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[+] Loki payload written to {args.output}")

if __name__ == "__main__":
    main()
