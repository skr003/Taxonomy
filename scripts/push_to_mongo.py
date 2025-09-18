#!/usr/bin/env python3
import argparse
import json
import os
from pymongo import MongoClient
from urllib.parse import quote_plus

def parse_args():
    parser = argparse.ArgumentParser(description="Push JSON logs to MongoDB")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--in-dir", required=True, help="Directory with *_mongo.json files")
    return parser.parse_args()

def main():
    args = parse_args()
    client = MongoClient(args.mongo_uri)
    db = client[args.db]
    collection = db[args.collection]

    files = [f for f in os.listdir(args.in_dir) if f.endswith("_mongo.json")]
    if not files:
        print(f"[!] No *_mongo.json files found in {args.in_dir}")
        return

    for f in files:
        path = os.path.join(args.in_dir, f)
        with open(path, "r") as infile:
            try:
                data = json.load(infile)
                collection.insert_one(data)
                print(f"[+] Inserted {f} into {args.db}.{args.collection}")
            except Exception as e:
                print(f"[!] Failed to insert {f}: {e}")

if __name__ == "__main__":
    main()
