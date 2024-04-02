import requests
import os
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor

print("Waiting for 25 seconds for EKV to reach eventual consistency. Please be patient.", end='', flush=True)
for _ in range(25):  # Loop 25 times for 25 seconds
    time.sleep(1)  # Wait for 1 second
    print('.', end='', flush=True)  # Print a dot for each second waited, without moving to a new line
print("\nDone waiting.")  # Move to a new line when done waiting

buckets_with_404 = set()

def process_url(items, json_file_name, session):
    global buckets_with_404
    encountered_404 = False

    # Select the first, middle, and last URL from the list
    if len(items) >= 3:
        urls_to_test = [items[0], items[len(items) // 2], items[-1]]
    else:
        urls_to_test = items  # If less than 3 items, test all

    for item in urls_to_test:
        source = item['source']
        destination = item['destination']
        hash256 = item['hash']
        url = 'https://shopflix-upload.akamaized.net' + source
        try:
            response = session.get(url, headers={"Accept": "text/html"}, allow_redirects=False)
            rresponse = response.status_code
            rlocation = response.headers.get('Location', None)

            if rresponse == 404:
                encountered_404 = True
                print(f"[{json_file_name}] Encountered 404 for URL {url}, hash {hash256}")
            elif rresponse != 301:
                print(f"[{json_file_name}] Status code {rresponse} is incorrect for URL {url}, hash {hash256}")
            elif rresponse == 301 and destination != rlocation:
                print(f"[{json_file_name}] Status code is correct, but the returned redirect {rlocation} is incorrect for incoming URL {url}. The correct redirect is {destination}. Please review the rules {hash256} uploaded to EKV")
            elif rresponse == 301 and destination == rlocation:
                print(f"[{json_file_name}] [{hash256}] All good")
        except Exception as e:
            print(f"[{json_file_name}] Error processing URL {url}: {e}")

    if encountered_404:
        buckets_with_404.add(json_file_name)

def main():
    json_dir = "validation_json"
    if not os.path.exists(json_dir):
        print(f"The specified directory does not exist: {json_dir}")
        sys.exit(1)

    json_files = [os.path.join(json_dir, f) for f in os.listdir(json_dir) if f.endswith('.json')]

    with ThreadPoolExecutor(max_workers=6) as executor:
        session = requests.Session()
        futures = [executor.submit(process_url, json.load(open(json_file)), os.path.basename(json_file), session) for json_file in json_files]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    # Summary of buckets with 404s
    if buckets_with_404:
        print("\nSummary of buckets containing URLs that returned a 404:")
        for bucket in sorted(buckets_with_404):
            print(bucket)
    else:
        print("\nNo buckets contained URLs that returned a 404.")

if __name__ == "__main__":
    main()
