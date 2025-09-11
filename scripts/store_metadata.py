#!/usr/bin/env python3
import argparse, sqlite3, json, os
parser = argparse.ArgumentParser()
parser.add_argument("--db", required=True)
parser.add_argument("--meta", required=True)
args = parser.parse_args()
os.makedirs(os.path.dirname(args.db), exist_ok=True)
conn = sqlite3.connect(args.db)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS artifacts
             (id TEXT PRIMARY KEY, path TEXT, type TEXT, volatility TEXT, priority TEXT, score INTEGER)''')
with open(args.meta) as f:
    data = json.load(f)
for a in data.get('prioritized', []):
    c.execute('REPLACE INTO artifacts (id,path,type,volatility,priority,score) VALUES (?,?,?,?,?,?)',
              (a.get('name'), a.get('path'), a.get('type'), a.get('volatility'), a.get('priority'), a.get('priority_score')))
conn.commit()
conn.close()
print('Stored metadata in', args.db)
