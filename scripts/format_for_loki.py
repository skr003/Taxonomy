import json, time, uuid

def main():
    with open("output/priority_list.json") as f:
        data = json.load(f)

    case_id = data.get("case_id", str(uuid.uuid4()))
    logs = []

    for i, artifact in enumerate(data.get("priority_list", [])):
        logs.append([
            str(int(time.time() * 1e9)),  # nanoseconds timestamp
            f"[PRIORITY {i}] {artifact}"
        ])

    loki_payload = [
        {
            "stream": {
                "job": "forensics",
                "case_id": case_id
            },
            "values": logs
        }
    ]

    with open("output/loki_payload.json", "w") as out:
        json.dump(loki_payload, out, indent=2)

if __name__ == "__main__":
    main()
