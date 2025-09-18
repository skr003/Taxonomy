#!/usr/bin/env python3
import os
import json
import argparse
import time

MAX_ENTRY_SIZE = 250 * 1024  # 250KB safe for Loki entries

def chunk_items(items, max_size=MAX_ENTRY_SIZE):
    """Split items[] into chunks under Loki entry size limit."""
    chunk, size = [], 0
    for item in items:
        item_str = json.dumps(item)
        item_size = len(item_str.encode())
        if size + item_size > max_size and chunk:
            yield chunk
            chunk, size = [], 0
        chunk.append(item)
        size += item_size
    if chunk:
        yield chunk

def to_loki_payload(data):
    category = data.get("category", "unknown")
    timestamp = data.get("timestamp", str(int(time.time())))
    items = data.get("items", [])
    for i, chunk in enumerate(chunk_items(items)):
        yield {
            "streams": [
                {
                    "stream": {
                        "category": category,
                        "batch_id": str(i),
                        "count": str(len(chunk))
                    },
                    "values": [
                        [
                            str(int(time.time() * 1e9)),  # nanoseconds
                            json.dumps({"timestamp": timestamp, "items": chunk})
                        ]
                    ]
                }
            ]
        }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    os.makedirs(args.out_dir, exist_ok=True)

    base = os.path.basename(args.input).replace(".json", "")
    for i, payload in enumerate(to_loki_payload(data)):
        out_path = os.path.join(args.out_dir, f"{base}_loki_part{i}.json")
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"[+] Loki payload written: {out_path}")

if __name__ == "__main__":
    main()
