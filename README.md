# Jenkins Forensic Pipeline (Sample Repo)

This sample repository provides a minimal, end-to-end Jenkins pipeline that uses **Jenkins**, **Python**, and **Grafana** (simulated) to:
- Collect forensic artifacts (simulated)
- Prioritize artifacts
- Format logs into JSON
- Store metadata in SQLite
- Push payloads to Grafana (simulated)
- Provide a ready-to-import mindmap JSON example

## How to run locally (without Jenkins)
```bash
python3 scripts/initialize.py --workspace ./forensic_workspace
python3 scripts/collect_agent.py --input sample_data/sample_input.json --out forensic_workspace/artifacts.json
python3 scripts/prioritize.py --in forensic_workspace/artifacts.json --out forensic_workspace/priority_list.json
python3 scripts/format_json.py --in forensic_workspace/artifacts.json --out forensic_workspace/formatted_logs.json
python3 scripts/store_metadata.py --db forensic_workspace/metadata.db --meta forensic_workspace/priority_list.json
python3 scripts/push_grafana.py --in forensic_workspace/formatted_logs.json --out forensic_workspace/grafana_payload.json
```

## Contents
- `Jenkinsfile` - Declarative Jenkins pipeline
- `scripts/` - Python stage scripts
- `sample_data/` - Example JSON input
- `grafana/` - Example Grafana dashboard JSON (stub)

## Notes
- This repo is a *template* and uses simulated collection and Grafana push steps.
- Replace the simulated pieces with real collectors and Grafana API calls for production.
