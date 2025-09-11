#!/usr/bin/env python3
import argparse, json, os
parser = argparse.ArgumentParser()
parser.add_argument("--in", dest='infile', required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
with open(args.infile) as f:
    data = json.load(f)
# Convert to standardized schema
formatted = {
    'case_id': data.get('case_id'),
    'items': []
}
for a in data.get('artifacts', []):
    formatted['items'].append({
        'id': a.get('name'),
        'path': a.get('path'),
        'type': a.get('type'),
        'volatility': a.get('volatility'),
        'collected_at': a.get('collected_at'),
        'size': a.get('size'),
    })
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(formatted, f, indent=2)
print('Wrote formatted logs to', args.out)
