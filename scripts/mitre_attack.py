#!/usr/bin/env python3
"""
mitre_clean_remove_name.py

Load an existing MITRE JSON (default: forensic_workspace/mitre_auth.json or
forensic_workspace/mitre_mapping.json), remove all "name" keys recursively,
and write a cleaned file next to the original with suffix ".clean.json".

Usage:
  python3 scripts/mitre_clean_remove_name.py \
      --input forensic_workspace/mitre_auth.json \
      --output forensic_workspace/mitre_auth.clean.json
"""

import argparse
import json
import os
from datetime import datetime
from typing import Any

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", "-i", default="forensic_workspace/mitre_auth.json",
                   help="Input MITRE JSON file to clean")
    p.add_argument("--output", "-o", default=None,
                   help="Output cleaned JSON file (default: input with .clean.json suffix)")
    return p.parse_args()

def remove_name_keys(obj: Any) -> Any:
    """
    Recursively remove any dictionary key equal to 'name'.
    Works for nested dicts and lists.
    """
    if isinstance(obj, dict):
        # build new dict without 'name'
        new = {}
        for k, v in obj.items():
            if k == "name":
                # skip it entirely
                continue
            new[k] = remove_name_keys(v)
        return new
    elif isinstance(obj, list):
        return [remove_name_keys(x) for x in obj]
    else:
        return obj

def main():
    args = parse_args()
    infile = args.input
    if not os.path.exists(infile):
        print(f"[ERROR] Input file not found: {infile}")
        return 2

    outpath = args.output
    if not outpath:
        base, ext = os.path.splitext(infile)
        outpath = f"{base}.clean{ext or '.json'}"

    with open(infile, "r") as fh:
        try:
            j = json.load(fh)
        except Exception as e:
            print(f"[ERROR] Failed to parse JSON {infile}: {e}")
            return 3

    cleaned = remove_name_keys(j)

    # Optionally add a small provenance field
    cleaned['_cleaned_at'] = datetime.utcnow().isoformat() + "Z"
    cleaned['_cleaned_from'] = os.path.basename(infile)

    # write out
    with open(outpath, "w") as fh:
        json.dump(cleaned, fh, indent=2)

    print(f"[OK] Wrote cleaned file without 'name' fields: {outpath}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
