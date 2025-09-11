#!/usr/bin/env python3
import argparse, json
parser = argparse.ArgumentParser()
parser.add_argument("--in", dest='infile', required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
with open(args.infile) as f:
    data = json.load(f)
# Simple rules engine
def score(a):
    score = 0
    if a.get('volatility') == 'volatile': score += 50
    if a.get('type') == 'memory': score += 30
    if 'auth' in a.get('name',''): score += 20
    # smaller size -> quicker to analyze
    score += max(0, 10 - (a.get('size',0)//10000))
    return score
for a in data.get('artifacts', []):
    a['priority_score'] = score(a)
    if a['priority_score'] >= 60:
        a['priority'] = 'high'
    elif a['priority_score'] >= 30:
        a['priority'] = 'medium'
    else:
        a['priority'] = 'low'
out = { 'case_id': data.get('case_id'), 'prioritized': data.get('artifacts') }
with open(args.out, 'w') as f:
    json.dump(out, f, indent=2)
print('Wrote priority list to', args.out)
