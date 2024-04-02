import json
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import sys

# Disable SSL warnings from 'requests'
requests.packages.urllib3.disable_warnings()

def upload_json_file(json_file_path, session):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
        url = 'https://shopflix-upload.akamaized.net/emea/upload'
        file_name_without_extension = os.path.splitext(os.path.basename(json_file_path))[0]
        headers = {"Content-Type": "application/json", "User-Agent": "custom-agent", "X-File-Name": file_name_without_extension}
        response = session.post(url, json=json_data, headers=headers, verify=False)
        print(response.headers)
    except Exception as e:
        print(f"Failed to upload {json_file_path}: {e}")

def upload_files_in_directory(json_output_dir, session):
    json_files = [os.path.join(json_output_dir, file) for file in os.listdir(json_output_dir) if file.endswith('.json')]
    num_threads = 2  # Example thread count
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(lambda file: upload_json_file(file, session), json_files)

if __name__ == "__main__":
    json_output_dir = 'json_buckets_with_jenkins'
    if not os.path.isdir(json_output_dir):
        print(f"The specified directory does not exist: {json_output_dir}")
        sys.exit(1)

    session = requests.Session()

    upload_files_in_directory(json_output_dir, session)
