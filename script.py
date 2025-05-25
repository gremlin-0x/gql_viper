import os
import json
import urllib.parse
import requests
from colorama import Fore, Style, init

from zap import get_proxies, get_message
from scripts.gql_viper.core import find_type, build_operations

init(autoreset=True)

DEFAULT_INTROSPECTION_QUERY = """query IntrospectionQuery {
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
            kind name ofType {
              kind name ofType {
                kind name
              }
            }
          }
        }
        type {
          kind name ofType {
            kind name ofType {
              kind name
            }
          }
        }
      }
      inputFields {
        name
        type {
          kind name ofType {
            kind name
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
        resp = requests.post(url, json={'query': query},
                             headers={'Content-Type': 'application/json'},
                             proxies=proxies, verify=False)
    else:
        resp = requests.get(url, params={'query': query},
                            proxies=proxies, verify=False)
    resp.raise_for_status()
    data = resp.json()
    if 'data' not in data or '__schema' not in data['data']:
        raise RuntimeError('No __schema in response')
    return data['data']['__schema']

def run_introspection(request_id: int, method: str, output_file: str = None, mode: str = 'inline'):
    print("[*] Starting introspection")
    proxies = get_proxies()

    msg = get_message(request_id)
    url = msg['requestHeader'].splitlines()[0].split()[1]

    # Force inline mode for GET
    actual_mode = 'inline' if method == 'GET' else mode

    introspection_dir = os.path.join(os.path.dirname(__file__), 'introspection')
    all_ops = []

    for fname in sorted(os.listdir(introspection_dir)):
        if not fname.endswith('.gql'):
            continue
        print(f"[*] Trying introspection query: {fname}")
        q = load_introspection_query(os.path.join(introspection_dir, fname))
        try:
            schema = perform_introspection_request(url, method, q, proxies)
            print(f"[*] Got schema:\n    • queryType: {schema.get('queryType')}\n    • mutationType: {schema.get('mutationType')}")
            print(f"[*] Types in schema: {len(schema.get('types', []))}")

            qtype = find_type(schema['types'], schema['queryType']['name'])

            # Safely resolve mutation type
            mutation_type_info = schema.get('mutationType')
            mtype = None
            if mutation_type_info and isinstance(mutation_type_info, dict):
                mutation_name = mutation_type_info.get('name')
                if mutation_name:
                    mtype = find_type(schema['types'], mutation_name)

            ops = build_operations(qtype, 'query', schema['types'], mode=actual_mode)
            if mtype:
                ops += build_operations(mtype, 'mutation', schema['types'], mode=actual_mode)

            all_ops.extend(ops)
        except Exception as e:
            print(f"[!] Failed with {fname}: {e}")
            continue

    if not all_ops:
        print("[!] No working introspection queries succeeded.")
        return

    print(f"\n[*] Generated {len(all_ops)} operations:")
    print("────────────────────────────────────────────")
    lines = []
    for idx, op in enumerate(all_ops, 1):
        if method == 'GET':
            encoded = urllib.parse.quote(op).replace('%20', '+')
            full = f"{url}?query={encoded}"
        else:
            full = json.dumps(op) if isinstance(op, dict) else json.dumps({"query": op})
        root_line = op if isinstance(op, str) else op.get('query', '')
        root_name = root_line.strip().split('{')[1].strip().split('(')[0].strip()
        print(f"[{idx}] {method}: {root_name}")
        print(full + "\n")
        lines.append(full)
    print("────────────────────────────────────────────")

    output_path = os.path.join(os.path.dirname(__file__), 'output.txt')
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"[+] Saved output to {output_path}")

