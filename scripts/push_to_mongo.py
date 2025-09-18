import os
import json
from pymongo import MongoClient

def push_file(client, db_name, collection_name, filepath):
    db = client[db_name]
    collection = db[collection_name]

    with open(filepath) as f:
        data = json.load(f)

    # If it's too large, split items
    if isinstance(data, dict) and "items" in data:
        batch_size = 500  # adjust to keep under 16MB
        items = data["items"]
        for i in range(0, len(items), batch_size):
            chunk = {
                "category": data.get("category"),
                "timestamp": data.get("timestamp"),
                "count": len(items[i:i+batch_size]),
                "items": items[i:i+batch_size]
            }
            collection.insert_one(chunk)
            print(f"[+] Inserted chunk {i//batch_size + 1} from {os.path.basename(filepath)}")
    else:
        collection.insert_one(data)
        print(f"[+] Inserted {os.path.basename(filepath)} into {db_name}.{collection_name}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--in-dir", required=True)
    args = parser.parse_args()

    client = MongoClient(args.mongo_uri)
    for file in os.listdir(args.in_dir):
        if file.endswith("_mongo.json"):
            push_file(client, args.db, args.collection, os.path.join(args.in_dir, file))

if __name__ == "__main__":
    main()
