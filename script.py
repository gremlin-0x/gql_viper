#!/usr/bin/env python3
import sys
import os

# Ensure project root is in sys.path so we can import zap
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import argparse
import json
import urllib.parse
import requests

from zap import get_proxies, get_message
from scripts.gql_viper.core import find_type, build_operations  # for building ops

# ----- Default Introspection Query -----
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

def perform_introspection_request(base_url, method, query, proxies):
    if method == 'POST':
        resp = requests.post(
            base_url,
            json={'query': query},
            headers={'Content-Type': 'application/json'},
            proxies=proxies
        )
    else:
        resp = requests.get(
            base_url,
            params={'query': query},
            proxies=proxies
        )
    resp.raise_for_status()
    data = resp.json()
    if 'data' not in data or '__schema' not in data['data']:
        raise RuntimeError('No __schema in response')
    return data['data']['__schema']

def main():
    parser = argparse.ArgumentParser(
        description='gql_viper script — GraphQL introspection via ZAP proxy'
    )
    parser.add_argument('-i', '--introspection-query', help='Custom .gql introspection file')
    parser.add_argument('-e', '--endpoint', required=True, help='Endpoint path (e.g. /graphql)')
    parser.add_argument('-m', '--method', choices=['GET','POST'], required=True, help='HTTP method')
    parser.add_argument('-o', '--output', help='Output file for queries')
    args = parser.parse_args()

    # get proxies from zap.py
    proxies = get_proxies()

    # Loop through every .gql in introspection dir
    introspection_dir = os.path.join(os.path.dirname(__file__), 'introspection')
    schema = None
    for fname in sorted(os.listdir(introspection_dir)):
        if not fname.endswith('.gql'):
            continue
        qpath = os.path.join(introspection_dir, fname)
        q = load_introspection_query(qpath)
        try:
            schema = perform_introspection_request(args.endpoint, args.method, q, proxies)
            break
        except Exception:
            continue

    if not schema:
        print('Failed to retrieve schema from any introspection file.')
        return

    types = schema['types']
    qtype = find_type(types, schema['queryType']['name'])
    mtype = find_type(types, schema.get('mutationType') or {})
    ops = build_operations(qtype, 'query', types) + build_operations(mtype, 'mutation', types)

    lines = []
    if args.method == 'GET':
        for op in ops:
            p = urllib.parse.quote(op).replace('%20','+')
            lines.append(f"{args.endpoint}?query={p}")
    else:
        for op in ops:
            lines.append(json.dumps({'query': op}))

    # print and save
    for l in lines:
        print(l)
    if args.output:
        with open(args.output, 'w') as f:
            f.write('\n'.join(lines))
        print(f"[+] Saved output to {args.output}")

if __name__ == '__main__':
    main()

