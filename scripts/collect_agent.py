#!/usr/bin/env python3
"""Simulated forensic agent: reads an input JSON and writes artifacts.json to out path"""
import argparse, json, os, sys
parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True, help="Sample input JSON")
parser.add_argument("--out", required=True, help="Output artifact JSON path")
args = parser.parse_args()
with open(args.input) as f:
    data = json.load(f)
# In a real agent you'd collect files, memory, processes. Here we annotate with timestamps and simulate packaging.
import datetime
for a in data.get('artifacts', []):
    a['collected_at'] = datetime.datetime.utcnow().isoformat() + 'Z'
    a['package'] = a['name'] + '.tgz'
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(data, f, indent=2)
print('Wrote artifacts to', args.out)
