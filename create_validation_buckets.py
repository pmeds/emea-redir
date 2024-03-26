import csv
import json
import os
from collections import defaultdict

def jenkins_one_at_a_time_hash(key):
    hash = 0
    # Ensure key is encoded as UTF-8 to match C's byte processing
    for byte in key.encode('utf-8'):
        hash += byte
        hash &= 0xFFFFFFFF  # Simulate 32-bit overflow
        hash += (hash << 10)
        hash &= 0xFFFFFFFF
        hash ^= (hash >> 6)
        hash &= 0xFFFFFFFF
    hash += (hash << 3)
    hash &= 0xFFFFFFFF
    hash ^= (hash >> 11)
    hash &= 0xFFFFFFFF
    hash += (hash << 15)
    hash &= 0xFFFFFFFF
    return hash


def create_json_buckets_with_jenkins(csv_input_path, json_output_dir, total_buckets=35000):
    # Ensure the output directory exists
    os.makedirs(json_output_dir, exist_ok=True)

    # Dictionary to hold entries temporarily
    buckets = {}

    with open(csv_input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            # Use the "from" field with the Jenkins hash function to generate a bucket number
            bucket_number = jenkins_one_at_a_time_hash(row['from']) % total_buckets + 1
            print(row['from'],bucket_number)
            # Construct the JSON object for the current row
            json_object = {
                "source": row['from'],
                "hash": row['hash'],
                "destination": row['to']
            }
            # Append the JSON object to the corresponding bucket list
            buckets.setdefault(bucket_number, []).append(json_object)

    # Variables to calculate statistics
    total_urls = 0
    min_urls = float('inf')
    max_urls = 0

    # Write each bucket's contents to a separate JSON file and gather statistics
    for bucket_number, entries in buckets.items():
        bucket_file_path = os.path.join(json_output_dir, f"bucket_{bucket_number}.json")
        with open(bucket_file_path, 'w', encoding='utf-8') as jsonfile:
            json.dump(entries, jsonfile, separators=(',', ':'))  # Updated part for compressed JSON

        # Update statistics
        num_urls = len(entries)
        total_urls += num_urls
        min_urls = min(min_urls, num_urls)
        max_urls = max(max_urls, num_urls)
        print(f"Bucket {bucket_number}: {num_urls} URLs")

    # Calculate and print average, minimum, and maximum
    average_urls = total_urls / len(buckets) if buckets else 0
    print(f"\nAverage number of URLs per bucket: {average_urls:.2f}")
    print(f"Minimum number of URLs in a bucket: {min_urls}")
    print(f"Maximum number of URLs in a bucket: {max_urls}")

csv_input_path = 'sample_modified_clean_csv_file.csv'
json_output_dir = 'validation_json'

create_json_buckets_with_jenkins(csv_input_path, json_output_dir)

print("JSON bucket files have been created using Jenkins hash function, and URL counts per bucket have been printed.")
