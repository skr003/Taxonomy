#!/usr/bin/env python3
import argparse, os, json
parser = argparse.ArgumentParser()
parser.add_argument("--workspace", required=True)
args = parser.parse_args()
os.makedirs(args.workspace, exist_ok=True)
# Write a small manifest
manifest = { "workspace": args.workspace }
with open(os.path.join(args.workspace, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print("Initialized workspace at", args.workspace)
