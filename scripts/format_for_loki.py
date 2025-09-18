import json, argparse, time, uuid

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True)
    parser.add_argument("--out", dest="output", required=True)
    args = parser.parse_args()

    with open(args.input) as f:
        data = json.load(f)

    case_id = data.get("case_id", str(uuid.uuid4()))
    logs = []

    for artifact in data.get("priority_list", []):
        logs.append([
            str(int(time.time() * 1e9)),
            json.dumps(artifact)
        ])

    loki_payload = [
        {
            "stream": {"job": "forensic_pipeline", "case_id": case_id},
            "values": logs
        }
    ]

    with open(args.output, "w") as f:
        json.dump(loki_payload, f, indent=2)

if __name__ == "__main__":
    main()
