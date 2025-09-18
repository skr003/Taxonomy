#!/usr/bin/env python3
import argparse
import json
import requests
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Push Loki payload JSON to Loki API")
    parser.add_argument("--in", dest="input", required=True, help="Input Loki payload JSON file")
    parser.add_argument("--url", dest="url", required=True, help="Loki API endpoint")
    return parser.parse_args()

def push_to_loki(file_path, url):
    with open(file_path, "r") as f:
        payload = json.load(f)

    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 204:
            print(f"[✓] Successfully pushed {file_path}")
        else:
            print(f"[!] Failed to push {file_path}: {resp.status_code} {resp.text}")
            sys.exit(1)
    except Exception as e:
        print(f"[!] Error pushing {file_path}: {e}")
        sys.exit(1)

def main():
    args = parse_args()
    push_to_loki(args.input, args.url)

if __name__ == "__main__":
    main()
