import argparse
import requests
import json
import urllib.parse

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
    if method == "POST":
        headers = {'Content-Type': 'application/json'}
        data = json.dumps({"query": query})
        response = requests.post(base_url, headers=headers, data=data)
    else:
        encoded_query = urllib.parse.quote(query).replace('%20', '+')
        url = f"{base_url}?query={encoded_query}"
        response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Introspection failed with status {response.status_code}: {response.text}")
    
    return response.json()

def find_type(types, name):
    for t in types:
        if t['name'] == name:
            return t
    return None

def build_arg_value(arg_type, types):
    kind = arg_type['kind']
    name = arg_type.get('name')
    of_type = arg_type.get('ofType')

    while kind in ['NON_NULL', 'LIST']:
        arg_type = of_type
        if not arg_type:
            break
        kind = arg_type['kind']
        name = arg_type.get('name')
        of_type = arg_type.get('ofType')

    if kind == 'SCALAR':
        if name == 'Int':
            return 1
        elif name == 'String':
            return '"example"'
        elif name == 'Boolean':
            return 'true'
        else:
            return 'null'
    elif kind == 'INPUT_OBJECT':
        input_obj = find_type(types, name)
        if not input_obj:
            return '{}'
        fields = []
        for input_field in input_obj.get('inputFields', []):
            field_value = build_arg_value(input_field['type'], types)
            fields.append(f"{input_field['name']}: {field_value}")
        return '{ ' + ', '.join(fields) + ' }'
    else:
        return 'null'

def build_return_fields(return_type, types, depth=0):
    while return_type.get('kind') in ['NON_NULL', 'LIST']:
        return_type = return_type.get('ofType', {})

    if return_type.get('kind') != 'OBJECT':
        return ''

    obj = find_type(types, return_type['name'])
    if not obj or not obj.get('fields'):
        return ''

    indent = '  ' * (depth + 1)
    inner_fields = []

    for field in obj['fields']:
        sub_return = build_return_fields(field['type'], types, depth + 1)
        if sub_return:
            inner_fields.append(f"{indent}{field['name']} {sub_return}")
        else:
            inner_fields.append(f"{indent}{field['name']}")

    joined_fields = '\n'.join(inner_fields)

    return f"{{\n{joined_fields}\n{'  '*depth}}}"


def build_operations(operation_type, operation_name, types):
    queries = []

    if not operation_type:
        return queries

    for field in operation_type.get('fields', []):
        field_name = field['name']
        args = []

        for arg in field.get('args', []):
            arg_val = build_arg_value(arg['type'], types)
            args.append(f"{arg['name']}: {arg_val}")

        args_str = ''
        if args:
            args_str = '(' + ', '.join(args) + ')'

        returns = build_return_fields(field['type'], types)

        query = f"""{operation_name} {{
  {field_name}{args_str} {returns}
}}"""
        queries.append(query)

    return queries

# ----- Main Execution -----

def main():
    parser = argparse.ArgumentParser(description="Automatic GraphQL Query Generator")
    parser.add_argument('-i', '--introspection-query', help='Path to file containing introspection query (optional)')
    parser.add_argument('-e', '--endpoint', required=True, help='GraphQL API endpoint (e.g., http://localhost:4000/graphql)')
    parser.add_argument('-m', '--method', choices=['GET', 'POST'], required=True, help='HTTP method to use (GET or POST)')
    parser.add_argument('-o', '--output', help='Output file to save results (optional)')

    args = parser.parse_args()

    query = load_introspection_query(args.introspection_query)
    print("[*] Performing introspection query...")

    introspection_result = perform_introspection(args.endpoint, args.method, query)

    with open('introspection_result.json', 'w') as f:
        json.dump(introspection_result, f, indent=2)

    print("[+] Saved introspection result to introspection_result.json")

    # Parse schema
    schema = introspection_result['data']['__schema']
    types = schema['types']

    query_type_name = schema['queryType']['name']
    mutation_type_name = schema['mutationType']['name'] if schema.get('mutationType') else None

    query_type = find_type(types, query_type_name)
    mutation_type = find_type(types, mutation_type_name) if mutation_type_name else None

    print("[*] Building operations...")

    queries = build_operations(query_type, "query", types)
    mutations = build_operations(mutation_type, "mutation", types)

    all_ops = queries + mutations

    output_lines = []

    print("[+] Generated queries/mutations:")
    for op in all_ops:
        if args.method == "GET":
            encoded = urllib.parse.quote(op).replace('%20', '+')
            final = f"{args.endpoint}?query={encoded}"
            print(final)
            output_lines.append(final)
        else:
            final = json.dumps({"query": op})
            print(final)
            output_lines.append(final)

    if args.output:
        with open(args.output, 'w') as f:
            for line in output_lines:
                f.write(line + '\n')
        print(f"[+] Saved output to {args.output}")

if __name__ == "__main__":
    main()

