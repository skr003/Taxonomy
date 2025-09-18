#!/usr/bin/env python3
import os
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    os.makedirs(args.out_dir, exist_ok=True)

    base = os.path.basename(args.input).replace(".json", "")
    out_path = os.path.join(args.out_dir, f"{base}_mongo.json")
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"[+] MongoDB JSON written: {out_path}")

if __name__ == "__main__":
    main()
