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
        return {'Int': 1, 'String': '\"example\"', 'Boolean': 'true'}.get(name, 'null')
    if kind == 'INPUT_OBJECT':
        obj = find_type(types, name)
        if not obj or not obj.get('inputFields'):
            return '{}'
        fields = []
        for fld in obj['inputFields']:
            val = build_arg_value(fld['type'], types)
            fields.append(f"{fld['name']}: {val}")
        return '{ ' + ', '.join(fields) + ' }'
    return 'null'

def build_return_fields(rtype, types, depth=0):
    while rtype.get('kind') in ('NON_NULL', 'LIST'):
        rtype = rtype.get('ofType', {})
    if rtype.get('kind') != 'OBJECT':
        return ''
    obj = find_type(types, rtype['name'])
    if not obj or not obj.get('fields'):
        return ''
    indent = '  ' * (depth + 1)
    inner = []
    for f in obj['fields']:
        sub = build_return_fields(f['type'], types, depth + 1)
        if sub:
            inner.append(f"{indent}{f['name']} {sub}")
        else:
            inner.append(f"{indent}{f['name']}")
    block = '\n'.join(inner)
    return f"{{\n{block}\n{'  '*depth}}}"

def build_operations(op_type, op_label, types):
    ops = []
    if not op_type or not op_type.get('fields'):
        return ops
    for fld in op_type['fields']:
        name = fld['name']
        args = []
        for a in fld.get('args', []):
            val = build_arg_value(a['type'], types)
            args.append(f"{a['name']}: {val}")
        arg_str = '(' + ', '.join(args) + ')' if args else ''
        ret = build_return_fields(fld['type'], types)
        ops.append(f"{op_label} {{\n  {name}{arg_str} {ret}\n}}")
    return ops

