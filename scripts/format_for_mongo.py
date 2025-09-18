#!/usr/bin/env python3
import argparse
import json
import os

def extract_metadata(item, category, timestamp):
    """Extract only metadata for MongoDB insertion (no full log content)."""
    return {
        "id": item.get("id"),
        "type": item.get("type"),
        "category": category,
        "path": item.get("meta", {}).get("path"),
        "tag": item.get("meta", {}).get("tag"),
        "status": item.get("meta", {}).get("status"),
        "timestamp": timestamp,
        "description": item.get("meta", {}).get("explanation"),
        "metadata": item.get("meta", {}).get("metadata", {}),
    }

def main():
    parser = argparse.ArgumentParser(description="Format logs for MongoDB ingestion.")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file (split log).")
    parser.add_argument("--out", dest="output", required=True, help="Output *_mongo.json file.")
    args = parser.parse_args()

    # Read input file
    with open(args.input, "r") as f:
        data = json.load(f)

    category = data.get("category")
    timestamp = data.get("timestamp")
    items = data.get("items", [])

    # Strip raw log entries and only keep metadata
    mongo_ready = [extract_metadata(item, category, timestamp) for item in items]

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Write mongo-formatted JSON
    with open(args.output, "w") as f:
        json.dump(mongo_ready, f, indent=2)

    print(f"[+] MongoDB payload written to {args.output}")

if __name__ == "__main__":
    main()
