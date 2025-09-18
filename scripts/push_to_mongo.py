# scripts/push_to_mongo.py
import argparse
import json
import os
from pymongo import MongoClient

def insert_file(coll, filepath, batch_size=1000):
    with open(filepath) as f:
        data = json.load(f)

    # If data is a dict with "items"
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
        for i in range(0, len(items), batch_size):
            chunk = items[i:i+batch_size]
            coll.insert_many(chunk)
            print(f"[+] Inserted {len(chunk)} docs from {os.path.basename(filepath)} (chunk {i//batch_size+1})")

    # If data is already a list
    elif isinstance(data, list):
        for i in range(0, len(data), batch_size):
            chunk = data[i:i+batch_size]
            coll.insert_many(chunk)
            print(f"[+] Inserted {len(chunk)} docs from {os.path.basename(filepath)} (chunk {i//batch_size+1})")

    else:
        # Single JSON object, insert as one doc
        coll.insert_one(data)
        print(f"[+] Inserted 1 doc from {os.path.basename(filepath)}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in-dir", required=True, help="Directory containing JSON files")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--collection", required=True, help="Collection name")
    args = parser.parse_args()

    client = MongoClient(args.mongo_uri)
    db = client[args.db]
    coll = db[args.collection]

    # Drop old collection before inserting new build
    coll.drop()
    print(f"[+] Dropped old collection {args.db}.{args.collection}")

    for file in os.listdir(args.in_dir):
        if file.endswith(".json"):
            filepath = os.path.join(args.in_dir, file)
            print(f"[+] Processing {filepath} ...")
            insert_file(coll, filepath)

    print("[+] All files pushed successfully.")

if __name__ == "__main__":
    main()
