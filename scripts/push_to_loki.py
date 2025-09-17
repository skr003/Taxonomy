#!/usr/bin/env python3
import argparse
import json
import requests

def push_to_loki(loki_url, payload_file):
    with open(payload_file, "r") as f:
        payload = json.load(f)
    headers = {"Content-Type": "application/json"}
    r = requests.post(loki_url, headers=headers, json=payload)
    if r.status_code == 204:
        print("[+] Logs successfully pushed to Loki")
    else:
        print(f"[!] Failed to push logs: {r.status_code} {r.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loki-url", required=True)
    parser.add_argument("--in", dest="input", required=True)
    args = parser.parse_args()

    push_to_loki(args.loki_url, args.input)
