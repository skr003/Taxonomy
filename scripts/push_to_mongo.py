import os
import json
from pymongo import MongoClient

def push_file(client, db_name, collection_name, filepath):
    db = client[db_name]
    collection = db[collection_name]

    with open(filepath) as f:
        data = json.load(f)

    # If file has multiple items, insert them individually
    if isinstance(data, dict) and "items" in data:
        docs = []
        for item in data["items"]:
            doc = {
                "category": data.get("category"),
                "timestamp": data.get("timestamp"),
                "item": item
            }
            docs.append(doc)

            # Insert in batches to avoid memory issues
            if len(docs) >= 500:  # batch size
                collection.insert_many(docs)
                print(f"[+] Inserted batch of {len(docs)} from {os.path.basename(filepath)}")
                docs = []

        if docs:
            collection.insert_many(docs)
            print(f"[+] Inserted final {len(docs)} docs from {os.path.basename(filepath)}")

    else:
        # Insert the whole thing if small enough
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
