#!/usr/bin/env python3
"""Forensic agent: collects live system data and writes artifacts JSON to --out path."""
import argparse, json, os, time, platform, socket, getpass, subprocess
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True, help="Output artifact JSON path")
args = parser.parse_args()

def try_psutil_collection():
    try:
        import psutil
    except Exception:
        return None
    data = {}
    data['host'] = platform.node()
    data['timestamp'] = time.time()
    data['user'] = getpass.getuser()
    data['os'] = platform.platform()
    # processes
    procs = []
    for p in psutil.process_iter(['pid','name','username','create_time']):
        info = p.info
        procs.append(info)
    data['processes'] = procs
    # connections
    try:
        conns = []
        for c in psutil.net_connections(kind='inet'):
            conns.append({'fd': c.fd, 'family': str(c.family), 'type': str(c.type), 'laddr': str(c.laddr), 'raddr': str(c.raddr), 'status': c.status, 'pid': c.pid})
        data['connections'] = conns
    except Exception:
        data['connections'] = []
    # memory
    try:
        vm = psutil.virtual_memory()._asdict()
        data['memory'] = vm
    except Exception:
        data['memory'] = {}
    return data

def fallback_shell_collection():
    data = {}
    data['host'] = platform.node()
    data['timestamp'] = time.time()
    data['user'] = getpass.getuser()
    data['os'] = platform.platform()
    # ps output
    try:
        p = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        data['ps_aux'] = p.stdout.splitlines()
    except Exception as e:
        data['ps_aux_error'] = str(e)
    # ss or netstat
    try:
        p = subprocess.run(['ss', '-tunap'], capture_output=True, text=True, timeout=10)
        data['net_stat'] = p.stdout.splitlines()
    except Exception:
        try:
            p = subprocess.run(['netstat', '-tunap'], capture_output=True, text=True, timeout=10)
            data['net_stat'] = p.stdout.splitlines()
        except Exception as e:
            data['net_stat_error'] = str(e)
    # lsof
    try:
        p = subprocess.run(['lsof', '-nP'], capture_output=True, text=True, timeout=15)
        data['lsof'] = p.stdout.splitlines()[:500]  # limit size
    except Exception as e:
        data['lsof_error'] = str(e)
    return data

data = try_psutil_collection()
if data is None:
    data = fallback_shell_collection()

# Add small metadata
data['collected_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
with open(args.out, 'w') as f:
    json.dump(data, f, indent=2)
print('Wrote artifacts to', args.out)
