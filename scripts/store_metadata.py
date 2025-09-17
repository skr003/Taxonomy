#!/usr/bin/env python3
import argparse
import json
from pymongo import MongoClient
from urllib.parse import quote_plus

def main():
    parser = argparse.ArgumentParser(description="Store metadata into MongoDB Atlas")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB Atlas connection string")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    args = parser.parse_args()

    # Escape username/password inside URI
    uri = args.mongo_uri
    if "://" in uri and "@" in uri.split("://", 1)[1]:
        scheme, rest = uri.split("://", 1)
        creds, hostpart = rest.split("@", 1)
        if ":" in creds:
            user, pwd = creds.split(":", 1)
            creds = f"{quote_plus(user)}:{quote_plus(pwd)}"
            uri = f"{scheme}://{creds}@{hostpart}"

    # Load JSON file
    with open(args.input, "r") as f:
        data = json.load(f)

    # Connect to Mongo
    db = client["TaxonomyDB"]
    collection = db["artifacts"]
    collection.insert_one(data)

    # Insert JSON
    if isinstance(data, list):
        collection.insert_many(data)
    else:
        collection.insert_one(data)

    print(f"[+] Inserted {args.input} into MongoDB Atlas")

if __name__ == "__main__":
    main()
