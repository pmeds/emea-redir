import requests
import dns.resolver
import hashlib
from urllib.parse import urlparse
import concurrent.futures
import os
import json
from threading import Lock
import sys
import time
from concurrent.futures import ThreadPoolExecutor


print("Waiting for 25 seconds for EKV to reach eventual consistency. Please be patient.", end='', flush=True)

for _ in range(25):  # Loop 15 times for 15 seconds
    time.sleep(1)  # Wait for 1 second
    print('.', end='', flush=True)  ### Print a dot for each second waited, without moving to a new line

print("\nDone waiting.")  # Move to a new line when done waiting


def _get_canonical_name(hostname_www):
    print(f'Attempting to get canonical name for {hostname_www}')
    resolver = dns.resolver.Resolver()
    try:
        canonical_name = resolver.resolve(hostname_www).canonical_name.to_unicode().rstrip('.')
        print(f'{hostname_www} has canonical name {canonical_name}')
        return canonical_name
    except dns.resolver.NXDOMAIN:
        print(f'Nonexistent domain {hostname_www}')
        return None


get_canonical_name = _get_canonical_name('shopflix-upload.akamaized.net')
print(get_canonical_name)

staging_host = get_canonical_name.replace('akamai', 'akamai-staging')
print(staging_host)


def resolveDNSA():
    domain = staging_host
    resolver = dns.resolver.Resolver()
    answer = resolver.resolve(domain, "A")
    return answer


resultDNSA = resolveDNSA()
answerA = ''

for item in resultDNSA:
    resultant_str = ''.join([str(item), answerA])

#print(resultant_str)


class HostHeaderSSLAdapter(requests.adapters.HTTPAdapter):
    def resolve(self, hostname):
        ips = resultant_str
        resolutions = {'shopflix-upload.akamaized.net': ips}
        #print(resolutions)
        return resolutions.get(hostname)

    def send(self, request, **kwargs):
        connection_pool_kwargs = self.poolmanager.connection_pool_kw
        result = urlparse(request.url)
        resolved_ip = self.resolve(result.hostname)

        if result.scheme == 'https' and resolved_ip:
            request.url = request.url.replace('https://' + result.hostname, 'https://' + resolved_ip)
            connection_pool_kwargs['server_hostname'] = result.hostname
            connection_pool_kwargs['assert_hostname'] = result.hostname
            request.headers['Host'] = result.hostname
        else:
            connection_pool_kwargs.pop('server_hostname', None)
            connection_pool_kwargs.pop('assert_hostname', None)

        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)


buckets_with_404 = set()
lock = Lock()

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
        with lock:
            buckets_with_404.add(json_file_name)


def main():
    json_dir = "validation_json"
    json_files = [os.path.join(json_dir, f) for f in os.listdir(json_dir) if f.endswith('.json')]

    # Within the main function, ensure sessions are created and passed appropriately
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        session = requests.Session()  # Consider creating just one session if all requests go to the same domain
        session.mount('https://', HostHeaderSSLAdapter())
        futures = [executor.submit(process_url, json.load(open(json_file)), os.path.basename(json_file), session) for
                   json_file in json_files]
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

