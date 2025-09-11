#!/usr/bin/env python3
import argparse, json, os
parser = argparse.ArgumentParser()
parser.add_argument("--in", dest='infile', required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
with open(args.infile) as f:
    data = json.load(f)
formatted = {'case_id': data.get('host'), 'collected_at': data.get('collected_at'), 'items': []}
procs = data.get('processes') or []
for p in procs:
    formatted['items'].append({'id': f"proc-{p.get('pid','')}", 'type': 'process', 'name': p.get('name'), 'username': p.get('username'), 'meta': p})
if data.get('ps_aux'):
    formatted['items'].append({'id':'ps_aux', 'type':'log', 'entries_count': len(data['ps_aux'])})
if data.get('net_stat'):
    formatted['items'].append({'id':'net_stat', 'type':'network', 'entries_count': len(data['net_stat'])})
if data.get('lsof'):
    formatted['items'].append({'id':'lsof', 'type':'system', 'entries_count': len(data['lsof'])})
os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(formatted, f, indent=2)
print('Wrote formatted logs to', args.out)
