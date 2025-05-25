# scripts/gql_viper/script.py
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import os
import json
import urllib.parse
import requests

from zap import get_proxies, get_message
from scripts.gql_viper.core import find_type, build_operations

DEFAULT_INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      kind
      name
      fields {
        name
        args {
          name
          type {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
              }
            }
          }
        }
        type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
            }
          }
        }
      }
      inputFields {
        name
        type {
          kind
          name
          ofType {
            kind
            name
          }
        }
      }
    }
  }
}
"""

def load_introspection_query(path):
    if not path:
        return DEFAULT_INTROSPECTION_QUERY
    with open(path, 'r') as f:
        return f.read()

def perform_introspection_request(url, method, query, proxies):
    if method == 'POST':
        resp = requests.post(url, json={'query': query}, headers={'Content-Type': 'application/json'}, proxies=proxies, verify=False)
    else:
        resp = requests.get(url, params={'query': query}, proxies=proxies, verify=False)
    resp.raise_for_status()
    data = resp.json()
    if 'data' not in data or '__schema' not in data['data']:
        raise RuntimeError('No __schema in response')
    return data['data']['__schema']

def run_introspection(request_id: int, method: str, output_file: str = None):
    print("[*] Starting introspection")
    proxies = get_proxies()

    msg = get_message(request_id)
    first_line = msg['requestHeader'].splitlines()[0]
    url = first_line.split()[1]  # full URL

    introspection_dir = os.path.join(os.path.dirname(__file__), 'introspection')
    all_ops = []

    for fname in sorted(os.listdir(introspection_dir)):
        if not fname.endswith('.gql'):
            continue
        path = os.path.join(introspection_dir, fname)
        print(f"[*] Trying introspection query: {fname}")
        gql = load_introspection_query(path)
        try:
            schema = perform_introspection_request(url, method, gql, proxies)
            types = schema['types']
            qtype = find_type(types, schema['queryType']['name'])
            mtype = find_type(types, schema.get('mutationType') or {})
            ops = build_operations(qtype, 'query', types) + build_operations(mtype, 'mutation', types)
            all_ops.extend(ops)
        except Exception as e:
            print(f"[!] Failed with {fname}: {e}")
            continue

    if not all_ops:
        print("[!] No working introspection queries succeeded.")
        return

    lines = []
    if method == 'GET':
        for op in all_ops:
            q = urllib.parse.quote(op).replace('%20', '+')
            lines.append(f"{url}?query={q}")
    else:
        for op in all_ops:
            lines.append(json.dumps({'query': op}))

    for line in lines:
        print(line)

    if output_file:
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        print(f"[+] Saved output to {output_file}")


