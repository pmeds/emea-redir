import json
import requests
import dns.resolver
import os
from concurrent.futures import ThreadPoolExecutor
import sys
from ratelimit import limits, sleep_and_retry

requests.packages.urllib3.disable_warnings()
# DNS resolution functions
def _get_canonical_name(hostname_www):
    print('Attempting to get canonical name for %s' % hostname_www)
    resolver = dns.resolver.Resolver()
    try:
        # Adjusting to 'CNAME' lookup might be necessary based on DNS resolver version
        canonical_name = resolver.resolve(hostname_www, 'CNAME')[0].target.to_text().rstrip('.')
    except dns.resolver.NXDOMAIN:
        print('Nonexistent domain %s' % hostname_www)
        return None
    except Exception as e:
        print(f'Error resolving canonical name for {hostname_www}: {e}')
        return None
    if canonical_name != hostname_www:
        print('%s has canonical name %s' % (hostname_www, canonical_name))
    return canonical_name

canonical_name = _get_canonical_name('paulm-sony.test.edgekey.net')
if canonical_name:
    staging_host = canonical_name.replace('akamaiedge', 'akamaiedge-staging')
else:
    sys.exit('Failed to get canonical name')

def resolveDNSA(staging_host):
    print(f'Resolving A records for {staging_host}')
    resolver = dns.resolver.Resolver()
    try:
        answer = resolver.resolve(staging_host, "A")
        return [item.to_text() for item in answer]
    except Exception as e:
        print(f'Error resolving A records for {staging_host}: {e}')
        return []

resolved_ips = resolveDNSA(staging_host)
if not resolved_ips:
    sys.exit('Failed to resolve A records')

class HostHeaderSSLAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, resolved_ips, *args, **kwargs):
        super(HostHeaderSSLAdapter, self).__init__(*args, **kwargs)
        self.resolved_ips = resolved_ips

    def send(self, request, **kwargs):
        hostname = request.url.split('//')[-1].split('/')[0]
        resolved_ip = self.resolved_ips[0]
        request.url = request.url.replace(hostname, resolved_ip)
        request.headers['Host'] = hostname
        return super(HostHeaderSSLAdapter, self).send(request, **kwargs)
# Define the rate limit: 39 calls per second
CALLS = 39
SECONDS = 1

@sleep_and_retry
@limits(calls=CALLS, period=SECONDS)
def upload_json_file(json_file_path, session):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
            #print(json_data)
        url = 'https://paulm-sony.test.edgekey.net/emea/upload'
        file_name_without_extension = os.path.splitext(os.path.basename(json_file_path))[0]
        headers = {"Content-Type": "application/json", "User-Agent": "custom-agent", "X-File-Name": file_name_without_extension, "Pragma": "akamai-x-im-trace, akamai-x-ew-debug-rp, akamai-x-ew-onclientrequest, akamai-x-ew-onclientresponse,akamai-x-ew-debug-subs, akamai-x-get-client-ip, akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-extracted-values, akamai-x-get-nonces, akamai-x-get-ssl-client-session-id, akamai-x-get-true-cache-key, akamai-x-serial-no, x-akamai-feo-state, X-Content, X-Hosts, akamai-x-get-request-id, akamai-x-ew-debug", "Akamai-EW-Trace": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ2Y2QiOiI0MTIyIiwia2lkIjo0LCJhY2wiOlsicGF1bG0tc29ueS50ZXN0LmVkZ2VrZXkubmV0Il0sImV4cCI6MTcxMTUxNTI3NiwiaWF0IjoxNzExNDcyMDc2LCJqdGkiOiIyMWEwYjhiMy0zNjZlLTQzYWQtOThiMC1iOWU2M2I3NGM2ZDcifQ.AWe01xw4AUfPBSj0BOwVRSqDIqBX9H5LWn9O_8RoX4JiHYyeIvnwtol6dN4q-Yzq9JJLYosFTm8tIRuhmqB9zTlA8y41re17Tr79xeMlwMk8wFy4_I--QsLe7IfRw2gluVG954OGUfxENmMpRTNmaeKBSr1RRpnKYKNtv2HKMDaTar2c6j_eRIAnGAfWVc84kDUHrhpphI1keYWcwmzWf8Ho4sxdVST6ZkxPRcc2bQ-QBuor-6yCjSQlv2xfLlx4gczlDr6C93mcEGz8LrSYBsn8eIwnSad_5IA9qTE8ef9aylkJy7SEAwLpyDAczCmz1yylArcbKt12Ozp8WkXNsg"}
        # print(headers)
        response = session.post(url, json=json_data, headers=headers, verify=False)
        rheaders = response.headers
        print(rheaders)
        #print(f"Uploaded {json_file_path}: {response.status_code}")
    except Exception as e:
        print(f"Failed to upload {json_file_path}: {e}")

def upload_files_in_directory(json_output_dir, session):
    json_files = [os.path.join(json_output_dir, file) for file in os.listdir(json_output_dir) if file.endswith('.json')]
    for json_file in json_files:
        upload_json_file(json_file, session)

if __name__ == "__main__":
    json_output_dir = 'json_buckets_with_jenkins'
    if not os.path.isdir(json_output_dir):
        print(f"The specified directory does not exist: {json_output_dir}")
        sys.exit(1)

    session = requests.Session()
    adapter = HostHeaderSSLAdapter(resolved_ips)
    session.mount('https://', adapter)

    upload_files_in_directory(json_output_dir, session)
