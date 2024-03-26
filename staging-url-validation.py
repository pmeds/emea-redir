import time
import pandas as pd
import requests
import dns.resolver
import hashlib
from urllib.parse import urlparse
import concurrent.futures
import os
import json

"""
print("Waiting for 15 seconds for EKV to reach eventual consistency. Please be patient.", end='', flush=True)

for _ in range(15):  # Loop 15 times for 15 seconds
    time.sleep(1)  # Wait for 1 second
    print('.', end='', flush=True)  ### Print a dot for each second waited, without moving to a new line

print("\nDone waiting.")  # Move to a new line when done waiting
"""

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


get_canonical_name = _get_canonical_name('paulm-sony.test.edgekey.net')
print(get_canonical_name)

staging_host = get_canonical_name.replace('akamaiedge', 'akamaiedge-staging')
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
        resolutions = {'paulm-sony.test.edgekey.net': ips}
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


def process_url(item, json_file_name):
    source = item['source']
    hash256 = item['hash']
    destination = item['destination']
    url = 'https://paulm-sony.test.edgekey.net' + source
    headers = {"Accept": "text/html"}

    session = requests.Session()
    session.mount('https://', HostHeaderSSLAdapter())
    response = session.get(url, headers=headers, allow_redirects=False)

    rresponse = response.status_code
    rlocation = response.headers.get('Location', None)
    source_hash = hashlib.sha256(source.encode('utf-8')).hexdigest()

    if rresponse != 301:
        print(f"[{json_file_name}] Status code {rresponse} is incorrect for URL {url}, hash {source_hash}")
    elif rresponse == 301 and destination != rlocation:
        print(f"[{json_file_name}] Status code is correct, but the returned redirect {rlocation} is incorrect for incoming URL {url}.")
        print(f"The correct redirect is {destination}. Please review the rules {source_hash} uploaded to EKV")
    elif rresponse == 301 and destination == rlocation:
        print(f"[{json_file_name}] [{hash256}]All good")

def main():
    json_dir = "json_buckets_with_jenkins"  # Hardcoded path to the directory
    json_files = [os.path.join(json_dir, file) for file in os.listdir(json_dir) if file.endswith('.json')]

    # Define the number of threads you want to use
    num_threads = 6  # Example thread count

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for json_file in json_files:
            json_file_name = os.path.basename(json_file)  # Extract just the file name
            with open(json_file, 'r', encoding='utf-8') as f:
                urls_list = json.load(f)
                # Submit all URLs in the current JSON file to the executor, passing the file name as well
                futures = [executor.submit(process_url, item, json_file_name) for item in urls_list]
                concurrent.futures.wait(futures)  # Wait for all futures in the current file

if __name__ == "__main__":
    main()
