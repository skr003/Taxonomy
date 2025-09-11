#!/usr/bin/env python3
"""Convert the formatted_logs.json into a simple mindmap JSON structure (suitable for import into tools that accept tree-JSON)"""
import argparse, json, os
parser = argparse.ArgumentParser()
parser.add_argument('--in', dest='infile', required=True)
parser.add_argument('--out', required=True)
args = parser.parse_args()
with open(args.infile) as f:
    data = json.load(f)
root = {'name': 'Forensic Pipeline - ' + str(data.get('case_id')), 'children': []}
buckets = {}
for item in data.get('items', []):
    t = item.get('type', 'other')
    buckets.setdefault(t, []).append(item)
for t, items in buckets.items():
    node = {'name': t, 'children': []}
    for it in items:
        node['children'].append({'name': it.get('id'), 'meta': {'path': it.get('path'), 'volatility': it.get('volatility'), 'size': it.get('size')}})
    root['children'].append(node)
os.makedirs(os.path.dirname(args.out), exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(root, f, indent=2)
print('Wrote mindmap JSON to', args.out)
