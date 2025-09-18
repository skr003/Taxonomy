#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime

MAX_LOKI_ENTRY = 250000  # 250 KB safety limit

def parse_args():
    parser = argparse.ArgumentParser(description="Convert split log JSON into Loki payload")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    parser.add_argument("--out", dest="output", required=True, help="Output Loki payload file")
    return parser.parse_args()

def to_nanos(ts: str) -> str:
    """Convert ISO8601 timestamp string to nanoseconds."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return str(int(dt.timestamp() * 1e9))

def split_large_entry(entry_str, max_size=MAX_LOKI_ENTRY):
    """Split large log entry into chunks under Loki's 256KB limit."""
    for i in range(0, len(entry_str), max_size):
        yield entry_str[i:i+max_size]

def convert_to_loki(data):
    streams = []
    timestamp = to_nanos(data.get("timestamp"))

    for item in data.get("items", []):
        labels = {
            "category": data.get("category", "unknown"),
            "id": item.get("id", "no-id"),
            "type": item.get("type", "na"),
            "tag": item.get("meta", {}).get("tag", "na"),
            "status": item.get("meta", {}).get("status", "na"),
        }

        log_line = json.dumps({
            "id": item.get("id"),
            "path": item.get("meta", {}).get("path"),
            "status": item.get("meta", {}).get("status"),
            "owner": item.get("meta", {}).get("owner"),
        }, ensure_ascii=False)

        if len(log_line.encode("utf-8")) > MAX_LOKI_ENTRY:
            for idx, chunk in enumerate(split_large_entry(log_line)):
                streams.append({
                    "stream": labels,
                    "values": [[timestamp, f"[chunk {idx+1}] {chunk}"]]
                })
        else:
            streams.append({
                "stream": labels,
                "values": [[timestamp, log_line]]
            })

    return {"streams": streams}

def main():
    args = parse_args()
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open(args.input, "r") as f:
        data = json.load(f)

    payload = convert_to_loki(data)

    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[+] Loki payload written to {args.output}")
    # Always keep full JSON for MongoDB (just reuse the original input)
    mongo_copy = args.output.replace("_loki.json", "_mongo.json")
    with open(mongo_copy, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[+] Full JSON stored for MongoDB: {mongo_copy}")

if __name__ == "__main__":
    main()
