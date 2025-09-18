#!/usr/bin/env python3
import os
import json
import argparse
import requests
import hashlib

MAX_ENTRY_SIZE = 250 * 1024  # 250KB safe limit for Loki entries

def chunk_items(items, max_size=MAX_ENTRY_SIZE):
    """Yield chunks of items that fit within Loki entry size limits."""
    chunk = []
    size = 0
    for item in items:
        item_str = json.dumps(item)
        if size + len(item_str.encode()) > max_size and chunk:
            yield chunk
            chunk = []
            size = 0
        chunk.append(item)
        size += len(item_str.encode())
    if chunk:
        yield chunk

def push_file(file_path, loki_url):
    with open(file_path, "r") as f:
        data = json.load(f)

    category = data.get("category", "unknown")
    timestamp = data.get("timestamp")

    items = data.get("items", [])
    total_chunks = 0

    for i, chunk in enumerate(chunk_items(items)):
        log_entry = {
            "streams": [
                {
                    "stream": {
                        "category": category,
                        "batch_id": str(i),
                        "count": str(len(chunk)),
                        "status": "collected"
                    },
                    "values": [
                        [
                            str(int(__import__("time").time() * 1e9)),  # nanosecond ts
                            json.dumps({"timestamp": timestamp, "items": chunk})
                        ]
                    ]
                }
            ]
        }

        r = requests.post(
            f"{loki_url}/loki/api/v1/push",
            headers={"Content-Type": "application/json"},
            data=json.dumps(log_entry)
        )

        if r.status_code != 204:
            print(f"[!] Failed to push chunk {i} of {file_path}: {r.text}")
        else:
            print(f"[+] Pushed {file_path} chunk {i} ({len(chunk)} items)")
            total_chunks += 1

    return total_chunks

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", required=True, help="Directory with JSON log files")
    parser.add_argument("--loki-url", required=True, help="Loki base URL (http://host:3100)")
    args = parser.parse_args()

    files = [os.path.join(args.in_dir, f) for f in os.listdir(args.in_dir) if f.endswith(".json")]
    if not files:
        print("[!] No JSON files found.")
        return

    for file_path in files:
        pushed = push_file(file_path, args.loki_url)
        print(f"[✓] Completed pushing {file_path} ({pushed} chunks)")

if __name__ == "__main__":
    main()
