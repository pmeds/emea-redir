import csv
import json
import os
from collections import defaultdict

def create_json_buckets(csv_input_path, json_output_dir):
    # Ensure the output directory exists
    os.makedirs(json_output_dir, exist_ok=True)

    # Dictionary to hold entries temporarily
    buckets = defaultdict(list)

    with open(csv_input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            hash_full = row['hash']
            hash_prefix = hash_full[:4]
            # Construct the JSON object for the current row
            json_object = {
                "hash": hash_full,
                "source": row['from'],
                "destination": row['to']
            }
            # Append the JSON object to the corresponding bucket list
            buckets[hash_prefix].append(json_object)

    # Write each bucket's contents to a separate JSON file
    for hash_prefix, entries in buckets.items():
        bucket_file_path = os.path.join(json_output_dir, f"bucket_{hash_prefix}.json")
        with open(bucket_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(entries, jsonfile, indent=4)

csv_input_path = 'sample_modified_clean_csv_file.csv'
json_output_dir = 'json_buckets'

create_json_buckets(csv_input_path, json_output_dir)

print("JSON bucket files have been created.")
