#!/usr/bin/env python3
import argparse
import json
from pymongo import MongoClient

def main():
    parser = argparse.ArgumentParser(description="Store metadata into MongoDB Atlas")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB Atlas connection string")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    args = parser.parse_args()

    # Load JSON file
    with open(args.input, "r") as f:
        data = json.load(f)

    # Connect to MongoDB
    client = MongoClient(args.mongo_uri)
    db = client["forensic_db"]          # database name
    collection = db["artifacts"]        # collection name

    # Insert JSON
    if isinstance(data, list):
        collection.insert_many(data)
    else:
        collection.insert_one(data)

    print(f"[+] Inserted {args.input} into MongoDB Atlas at collection 'artifacts'")

if __name__ == "__main__":
    main()
