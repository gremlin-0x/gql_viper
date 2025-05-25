#!/usr/bin/env python3

import argparse
import json
import os
import urllib.parse
import requests

from zap import get_proxies, get_message

# Default introspection
DEFAULT_INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    types { ... }
  }
}
"""

def load_introspection_query(path):
    if not path:
        return DEFAULT_INTROSPECTION_QUERY
    with open(path) as f:
        return f.read()

def perform_introspection_request(base_url, method, query, proxies):
    if method == 'POST':
        resp = requests.post(
            base_url,
            json={'query': query},
            proxies=proxies,
            headers={'Content-Type':'application/json'}
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
        description='viper.py — GraphQL introspection via ZAP proxy'
    )
    parser.add_argument('-i', '--introspection-query', help='Custom .gql introspection file')
    parser.add_argument('-e', '--endpoint',            required=True, help='Endpoint path (e.g. /graphql)')
    parser.add_argument('-m', '--method',   choices=['GET','POST'], required=True, help='HTTP method')
    parser.add_argument('-o', '--output',               help='Output file for queries')
    args = parser.parse_args()

    # fetch URL and proxies via zap.py
    schema = None
    proxies = get_proxies()
    # Loop every .gql in scripts/gql_viper/introspection
    introspection_dir = os.path.join(os.path.dirname(__file__), 'scripts', 'gql_viper', 'introspection')
    for fname in sorted(os.listdir(introspection_dir)):
        if not fname.endswith('.gql'):
            continue
        q = load_introspection_query(os.path.join(introspection_dir, fname))
        try:
            schema = perform_introspection_request(args.endpoint, args.method, q, proxies)
            break
        except Exception:
            continue

    if not schema:
        print('Failed to retrieve schema from any introspection file.')
        return

    # build operations
    from scripts.gql_viper.script import find_type, build_operations
    types = schema['types']
    qtype = find_type(types, schema['queryType']['name'])
    mtype = find_type(types, schema.get('mutationType') or {})
    ops = build_operations(qtype, 'query', types) + build_operations(mtype, 'mutation', types)

    # output
    lines = []
    if args.method == 'GET':
        for op in ops:
            p = urllib.parse.quote(op).replace('%20','+')
            lines.append(f"{args.endpoint}?query={p}")
    else:
        for op in ops:
            lines.append(json.dumps({'query':op}))

    # print & save
    for l in lines:
        print(l)
    if args.output:
        with open(args.output,'w') as f:
            f.write('\n'.join(lines))
        print(f"[+] Saved output to {args.output}")

if __name__ == '__main__':
    main()

