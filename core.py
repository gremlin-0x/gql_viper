# scripts/gql_viper/core.py

def find_type(types, name):
    for t in types:
        if t['name'] == name:
            return t
    return None


def build_arg_value(arg_type, types):
    kind = arg_type['kind']
    name = arg_type.get('name')
    of_type = arg_type.get('ofType')

    while kind in ('NON_NULL', 'LIST') and of_type:
        arg_type = of_type
        kind = arg_type['kind']
        name = arg_type.get('name')
        of_type = arg_type.get('ofType')

    if kind == 'SCALAR':
        return {
            'Int': '1',
            'Float': '1.0',
            'String': '"example"',
            'Boolean': 'true',
            'ID': '"1"',
        }.get(name, 'null')

    elif kind == 'INPUT_OBJECT':
        input_obj = find_type(types, name)
        if not input_obj:
            return '{}'
        fields = []
        for f in input_obj.get('inputFields', []):
            val = build_arg_value(f['type'], types)
            fields.append(f"{f['name']}: {val}")
        return '{ ' + ', '.join(fields) + ' }'

    return 'null'


def build_arg_json(arg_type, types):
    kind = arg_type['kind']
    name = arg_type.get('name')
    of_type = arg_type.get('ofType')

    while kind in ('NON_NULL', 'LIST') and of_type:
        arg_type = of_type
        kind = arg_type['kind']
        name = arg_type.get('name')
        of_type = arg_type.get('ofType')

    if kind == 'SCALAR':
        return {
            'Int': 1,
            'Float': 1.0,
            'String': "example",
            'Boolean': True,
            'ID': "1",
        }.get(name, None)

    elif kind == 'INPUT_OBJECT':
        obj = find_type(types, name)
        if not obj:
            return {}
        return {
            field['name']: build_arg_json(field['type'], types)
            for field in obj.get('inputFields', [])
        }

    return None


def build_return_fields(return_type, types, depth=0):
    while return_type.get('kind') in ('NON_NULL', 'LIST'):
        return_type = return_type.get('ofType', {})

    if return_type.get('kind') != 'OBJECT':
        return ''

    obj = find_type(types, return_type.get('name'))
    if not obj or not obj.get('fields'):
        return ''

    indent = '  ' * (depth + 1)
    fields = []
    for field in obj['fields']:
        nested = build_return_fields(field['type'], types, depth + 1)
        if nested:
            fields.append(f"{indent}{field['name']} {nested}")
        else:
            fields.append(f"{indent}{field['name']}")
    return "{\n" + '\n'.join(fields) + f"\n{'  '*depth}}}"


def build_operations(root_type, op_label, types, mode="inline"):
    if not root_type or not root_type.get('fields'):
        return []

    ops = []

    for field in root_type['fields']:
        name = field['name']
        args = field.get('args', [])
        ret = build_return_fields(field['type'], types)

        if mode == "inline":
            call_args = ''
            if args:
                arg_pairs = [
                    f"{arg['name']}: {build_arg_value(arg['type'], types)}"
                    for arg in args
                ]
                call_args = f"({', '.join(arg_pairs)})"
            query = f"{op_label} {{\n  {name}{call_args} {ret}\n}}"
            ops.append(query)

        elif mode == "variables":
            var_defs = []
            var_body = {}
            for arg in args:
                typename = build_variable_type(arg['type'])
                var_defs.append(f"${arg['name']}: {typename}")
                var_body[arg['name']] = build_arg_json(arg['type'], types)

            op_vars = f"({', '.join(var_defs)})" if var_defs else ""
            call_args_parts = []
            for arg in args:
                arg_name = arg['name']
                call_args_parts.append(f"{arg_name}: ${arg_name}")
            call_args = f"({', '.join(call_args_parts)})" if call_args_parts else ""
            query = {
                "query": f"{op_label} {name}{op_vars} {{\n  {name}{call_args} {ret}\n}}",
                "operationName": name,
                "variables": var_body
            }
            ops.append(query)

    return ops


def build_variable_type(arg_type):
    kind = arg_type['kind']
    name = arg_type.get('name')
    of_type = arg_type.get('ofType')

    if kind == 'NON_NULL':
        return build_variable_type(of_type) + '!'
    elif kind == 'LIST':
        return '[' + build_variable_type(of_type) + ']'
    else:
        return name or ''

