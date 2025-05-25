# gql\_viper

`gql_viper` is a GraphQL introspection and query generator tool designed to automate and simplify GraphQL testing using the OWASP ZAP proxy.

## Features

* Sends introspection queries through ZAP
* Automatically builds queries and mutations from the schema
* Supports both inline and variable-based GraphQL modes
* Replays and modifies generated queries

## Usage

This tool is meant to be called via the [aspiti](https://github.com/gremlin-0x/aspiti) CLI.

To introspect a GraphQL API (with inline queries):

```bash
python cli.py gql -i 76 -m POST -o output.txt
```

To generate queries using variables mode:

```bash
python cli.py gql -i 76 -m POST --mode variables -o output.txt
```

## Directory Layout

```
./scripts/gql_viper
├── core.py
├── script.py
├── introspection/
│   ├── query_01.gql
│   └── query_02.gql
└── output.txt
```

## Requirements

* Python 3.8+
* `colorama`
* `requests`
* ZAP proxy running and accessible

## Tested On

This tool has been successfully tested against the following PortSwigger GraphQL labs:

* **Accessing private GraphQL posts**
* **Accidental exposure of private GraphQL fields**
* **Finding a hidden GraphQL endpoint**
* **Bypassing GraphQL brute force protections**
* **Performing CSRF exploits over GraphQL**

## License

MIT

