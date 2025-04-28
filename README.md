# GraphQL Query Generator

An **automated GraphQL query builder** that:

- Fetches the GraphQL schema via introspection.
- Parses available **queries** and **mutations**.
- Auto-generates working GraphQL queries/mutations:
  - Expands arguments properly (including input objects).
  - Expands nested return fields properly.
- Outputs them either as:
  - URL-encoded queries for **GET** requests.
  - JSON request bodies for **POST** requests.

---

## Features

- Performs GraphQL introspection automatically.
- Builds real, working queries with nested fields and input objects.
- Supports both **GET** (URL encoding) and **POST** modes.
- Optionally saves output to a file.
- Default fallback introspection query built-in (can supply custom).
- Clean CLI interface.

---

## Requirements

- Python 3.6+
- `requests` module

Install `requests` if needed:

```bash
pip install requests
```

## Usage
```bash
python3 viper.py -e ENDPOINT -m METHOD [options]
```

### Required Arguments

| Flag | Description |
| ---- | ----------- |
| `-e`, `--endpoint` | Target GraphQL endpoint URL (e.g., `http://localhost:4000/graphql`) |
| `-m`, `--method` | HTTP request method to use (`GET` or `POST`) |

### Optional Arguments

| Flag | Description |
| ---- | ----------- |
| `-i`, `--introspection-query` | Path to a custom introspection query `.gql` file (if omitted, uses a built-in query) |
| `-o`, `--output` | Path to output file to save the generated queries |

## Example Usage

### 1. Basic `POST` Mode (default introspection query)
```bash
python3 viper.py -e http://example.com/graphql -m POST
```

### 2. Basic `GET` Mode + Save output
```bash
python3 viper.py -e http://example.com/graphql -m GET -o output.txt
```

### 3. Using a Custom Introspection Query
```bash
python3 viper.py -i my_introspection.gql -e http://example.com/graphql -m POST
```

## Output Format
- `GET` mode outputs URL-encoded queries like:
  ```
  /api?query=query+%7B+getUser%28id%3A+1%29+%7B+id+username+%7D+%7D
  ```
- `POST` mode outputs GraphQL request bodies like:
  ```graphql
  {"query":"query { getUser(id: 1) { id username } }"}
  ```

## License

This project is provided "as-is" for educational and penetration testing use only.
