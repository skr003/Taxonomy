# scripts/push_to_mongo.py
import argparse
import json
import os
from pymongo import MongoClient
from bson import json_util

MAX_BSON_SIZE = 16 * 1024 * 1024  # 16MB

def safe_insert(coll, doc, filename, idx):
    """Ensure no single document exceeds BSON size limit"""
    raw = json_util.dumps(doc).encode("utf-8")
    if len(raw) < MAX_BSON_SIZE:
        coll.insert_one(doc)
        print(f"[+] Inserted single doc from {filename} (part {idx})")
    else:
        # If still too large, split arrays inside
        if isinstance(doc, dict) and "items" in doc and isinstance(doc["items"], list):
            items = doc["items"]
            mid = len(items) // 2
            left = {**doc, "items": items[:mid]}
            right = {**doc, "items": items[mid:]}
            safe_insert(coll, left, filename, f"{idx}.L")
            safe_insert(coll, right, filename, f"{idx}.R")
        else:
            raise ValueError(
                f"[!] Document from {filename} part {idx} is too large "
                "and cannot be split automatically."
            )

def insert_file(coll, filepath):
    with open(filepath) as f:
        data = json.load(f)

    if isinstance(data, list):
        for i, doc in enumerate(data):
            safe_insert(coll, doc, filepath, i)
    else:
        safe_insert(coll, data, filepath, 0)

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
