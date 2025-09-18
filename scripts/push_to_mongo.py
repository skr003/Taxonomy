#!/usr/bin/env python3
import os
import json
import argparse
from pymongo import MongoClient
from urllib.parse import quote_plus

def push_to_mongo(mongo_uri, db_name, collection_name, input_dir):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    print(f"[!] Dropping database '{db_name}' before inserting new logs...")
    client.drop_database(db_name)

    inserted = 0
    for file in os.listdir(input_dir):
        if not file.endswith(".json"):
            continue
        file_path = os.path.join(input_dir, file)
        with open(file_path, "r") as f:
            data = json.load(f)

        # If file contains multiple docs, insert_many; else insert_one
        if isinstance(data, list):
            collection.insert_many(data)
            print(f"[+] Inserted {len(data)} docs from {file}")
            inserted += len(data)
        else:
            collection.insert_one(data)
            print(f"[+] Inserted 1 doc from {file}")
            inserted += 1

    print(f"[✓] Completed pushing logs: {inserted} documents inserted.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--collection", required=True, help="Collection name")
    parser.add_argument("--in-dir", required=True, help="Directory with JSON logs")
    args = parser.parse_args()

    push_to_mongo(args.mongo_uri, args.db, args.collection, args.in_dir)

if __name__ == "__main__":
    main()
