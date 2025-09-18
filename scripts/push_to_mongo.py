import os
import json
import argparse
from pymongo import MongoClient
import gridfs
from bson import BSON
from bson.errors import InvalidDocument


MAX_BSON_SIZE = 16_000_000  # MongoDB hard limit (~16MB)


def is_too_large(doc):
    """Check if a document exceeds BSON max size."""
    try:
        return len(BSON.encode(doc)) > MAX_BSON_SIZE
    except InvalidDocument:
        return True


def push_file(client, db_name, collection_name, filepath):
    db = client[db_name]
    collection = db[collection_name]
    fs = gridfs.GridFS(db, collection="Artifacts_raw")

    with open(filepath) as f:
        data = json.load(f)

    filename = os.path.basename(filepath)

    # Case 1: If entire doc fits → insert directly
    if not is_too_large(data):
        collection.insert_one(data)
        print(f"[+] Inserted {filename} as single doc into {db_name}.{collection_name}")
        return

    # Case 2: If "items" exists, try splitting into smaller docs
    if isinstance(data, dict) and "items" in data:
        items = data["items"]
        batch = []
        for item in items:
            doc = {
                "category": data.get("category"),
                "timestamp": data.get("timestamp"),
                "item": item
            }
            if is_too_large(doc):
                # Case 3: If even single item too large → fallback to GridFS
                print(f"[!] Oversized item in {filename}, storing in GridFS...")
                fs.put(json.dumps(item).encode("utf-8"),
                       filename=f"{filename}_oversized_item.json")
            else:
                batch.append(doc)

                if len(batch) >= 500:  # batch insert
                    collection.insert_many(batch)
                    print(f"[+] Inserted batch of {len(batch)} from {filename}")
                    batch = []

        if batch:
            collection.insert_many(batch)
            print(f"[+] Inserted final {len(batch)} docs from {filename}")
        return

    # Case 3: Fallback → Store whole file in GridFS
    print(f"[!] {filename} too large, storing in GridFS...")
    with open(filepath, "rb") as f:
        fs.put(f, filename=filename)
    print(f"[+] Stored {filename} in GridFS collection 'Artifacts_raw'")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--in-dir", required=True)
    args = parser.parse_args()

    client = MongoClient(args.mongo_uri)

    for file in os.listdir(args.in_dir):
        if file.endswith("_mongo.json"):
            push_file(client, args.db, args.collection,
                      os.path.join(args.in_dir, file))


if __name__ == "__main__":
    main()
