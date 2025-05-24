#!/usr/bin/env python3
# viper.py

import argparse
import json
import urllib.parse

from zap import get_proxies
import requests

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

# ----- Helpers -----

def load_introspection_query(file_path):
    if not file_path:
        return DEFAULT_INTROSPECTION_QUERY
    with open(file_path, 'r') as f:
        return f.read()

def perform_introspection(base_url, method, query):
    """
    Uses ZAP proxy configuration via zap.get_proxies()
    to send the introspection query.
    """
    proxies = get_proxies()
    if method == "POST":
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"query": query})
        response = requests.post(base_url,
                                 headers=headers,
                                 data=data,
                                 proxies=proxies)
    else:
        encoded = urllib.parse.quote(query).replace('%20', '+')
        url = f"{base_url}?query={encoded}"
        response = requests.get(url, proxies=proxies)

    if response.status_code != 200:
        raise RuntimeError(f"Introspection failed ({response.status_code}): {response.text}")
    return response.json()

# (the rest of find_type, build_arg_value, build_return_fields, build_operations stay unchanged) …

def main():
    parser = argparse.ArgumentParser(
        description="Automatic GraphQL Query Generator (using ZAP proxy)"
    )
    parser.add_argument('-i', '--introspection-query',
                        help='Path to custom introspection query (.gql)')
    parser.add_argument('-e', '--endpoint', required=True,
                        help='GraphQL API endpoint (e.g., http://localhost:4000/graphql)')
    parser.add_argument('-m', '--method', choices=['GET','POST'], required=True,
                        help='HTTP method for introspection')
    parser.add_argument('-o', '--output',
                        help='File to save generated queries')

    args = parser.parse_args()

    gql = load_introspection_query(args.introspection_query)
    print("[*] Performing introspection through ZAP proxy…")
    result = perform_introspection(args.endpoint, args.method, gql)

    with open('introspection_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("[+] Saved introspection_result.json")

    schema = result['data']['__schema']
    types = schema['types']
    qtype = find_type(types, schema['queryType']['name'])
    mtype = find_type(types, schema.get('mutationType') or {})

    print("[*] Building operations…")
    ops = build_operations(qtype, "query", types) + build_operations(mtype, "mutation", types)

    output_lines = []
    if args.method == "GET":
        for op in ops:
            p = urllib.parse.quote(op).replace('%20','+')
            line = f"{args.endpoint}?query={p}"
            print(line)
            output_lines.append(line)
    else:
        for op in ops:
            line = json.dumps({"query": op})
            print(line)
            output_lines.append(line)

    if args.output:
        with open(args.output, 'w') as f:
            f.write("\n".join(output_lines))
        print(f"[+] Saved output to {args.output}")

if __name__ == "__main__":
    main()

