#!/usr/bin/env python3
import argparse
from pymongo import MongoClient

def query_metadata(mongo_uri):
    client = MongoClient(mongo_uri)
    db = client.forensicDB
    collection = db.metadata

    print("[+] High-priority evidentiary artifacts:")
    for doc in collection.find({"priority": "high"}):
        print(f" - {doc['component']} @ {doc['path']} (tags: {doc.get('evidentiary_tags')})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True)
    args = parser.parse_args()

    query_metadata(args.mongo_uri)
