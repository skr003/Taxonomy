import json
import argparse
from pymongo import MongoClient

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mongo-uri", required=True, help="MongoDB Atlas connection URI")
    parser.add_argument("--in", dest="input", required=True, help="Input JSON file")
    args = parser.parse_args()

    # Load input JSON
    with open(args.input, "r") as f:
        data = json.load(f)

    # Connect to MongoDB
    client = MongoClient(args.mongo_uri)

    # Explicitly select DB and Collection
    db = client["TaxonomyDB"]
    collection = db["Artifacts"]

    # Insert
    result = collection.insert_one(data)
    print(f"[+] Inserted document with _id: {result.inserted_id}")

if __name__ == "__main__":
    main()
