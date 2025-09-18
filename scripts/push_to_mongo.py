# scripts/push_to_mongo.py
import argparse
import json
import os
from pymongo import MongoClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--collection", required=True, help="Collection name")
    args = parser.parse_args()

    client = MongoClient(args.mongo_uri)
    db = client[args.db]
    coll = db[args.collection]

    # Drop old data before inserting new
    coll.drop()

    with open(args.input) as f:
        data = json.load(f)

    # If the file contains an array of logs
    if isinstance(data, list):
        # Split into chunks of 1000 (tunable)
        batch_size = 1000
        for i in range(0, len(data), batch_size):
            chunk = data[i:i+batch_size]
            coll.insert_many(chunk)
            print(f"[+] Inserted chunk {i//batch_size + 1}")
    else:
        # If it's a dict with items
        items = data.get("items", [])
        batch_size = 1000
        for i in range(0, len(items), batch_size):
            chunk = items[i:i+batch_size]
            coll.insert_many(chunk)
            print(f"[+] Inserted {len(chunk)} docs")

    print("[+] All data pushed successfully.")

if __name__ == "__main__":
    main()
