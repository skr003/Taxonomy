#!/usr/bin/env python3
"""Simulated push to Grafana: writes a payload file that could be ingested by Grafana Loki or datasource.
In production, replace this with HTTP calls to Grafana/Loki or write to a real datasource.
"""
import argparse, json, os
parser = argparse.ArgumentParser()
parser.add_argument("--in", dest='infile', required=True)
parser.add_argument("--out", required=True, help='Local payload file to write (simulated)')
args = parser.parse_args()
with open(args.infile) as f:
    data = json.load(f)
payload = {
    'dashboard_ingest': True,
    'case_id': data.get('case_id'),
    'items_count': len(data.get('items', [])),
    'items': data.get('items', [])
}
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(payload, f, indent=2)
print('Wrote simulated Grafana payload to', args.out)
