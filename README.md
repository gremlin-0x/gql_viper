# Viper — Automatic GraphQL Query Generator (via ZAP Proxy)

**`viper.py`** is a standalone Python script that:

* Runs a GraphQL introspection query through your ZAP proxy
* Discovers the schema and automatically builds representative `query` and `mutation` operations
* Prints them to STDOUT and optionally writes them to a file

---

## Features

* **ZAP-driven**
  All HTTP traffic is routed through your ZAP proxy using its host/port/API-key settings (via a shared `zap.py` wrapper).

* **Introspection fallback**
  You can supply a custom `.gql` introspection query; otherwise the script uses the built-in default.

* **GET or POST**
  Supports both GET-encoded and POST-JSON methods for the introspection call.

* **Output options**
  • Always saves the raw introspection JSON to `introspection_result.json`
  • Prints all generated operations to the console
  • Optionally writes them to a text file via `-o`

---

## Requirements

* Python 3.6+
* The `requests` library
* A working `zap.py` in the same directory that provides `get_proxies()`

Install dependencies with:

```bash
pip install requests
```

---

## Setup & Structure

```text
project-root/
├── zap.py                      # ZAP API & proxy helper
├── viper.py                    # This GraphQL introspection generator
├── introspection_result.json   # Generated each run
└── optionally: output file     # If -o is used
```

Ensure `zap.py` is located alongside `viper.py` so it can load your ZAP config.

---

## Usage

Make the script executable:

```bash
chmod +x viper.py
```

Run it:

```bash
./viper.py \
  -i path/to/custom_introspection.gql \
  -e http://localhost:4000/graphql \
  -m POST \
  -o generated_queries.txt
```

### Arguments

* `-i, --introspection-query`
  Path to a `.gql` file containing your introspection query.
  If omitted, the built-in default is used.

* `-e, --endpoint` **(required)**
  Full URL of the GraphQL endpoint (e.g. `http://localhost:4000/graphql`).

* `-m, --method` **(required)**
  HTTP method for the introspection request: `GET` or `POST`.

* `-o, --output`
  Path to save the generated operations (one per line). If omitted, operations are only printed.

---

## Examples

Basic POST introspection, print only:

```bash
./viper.py -e http://api.test/graphql -m POST
```

With custom query and save to file:

```bash
./viper.py \
  -i introspection_custom.gql \
  -e http://api.test/graphql \
  -m GET \
  -o queries.txt
```

---

## How It Works

1. **Load or default introspection**: parses provided `.gql` or falls back to `DEFAULT_INTROSPECTION_QUERY`.
2. **Send through ZAP**: uses `get_proxies()` from `zap.py` to route via your ZAP proxy.
3. **Save raw schema**: writes full JSON to `introspection_result.json`.
4. **Build operations**: extracts `query` and `mutation` types, constructs field payloads via `build_operations()`.
5. **Output**: prints and optionally writes each operation line by line.

---

## Notes

* Ensure your `config.yaml` is set up via `aspiti config` or manually, so `zap.py` can read your ZAP settings.
* This script is part of a larger ZAP automation toolkit but also functions standalone for quick GraphQL schema exploration.

---

## License

Provided "as-is" for security testing and educational use. Always obtain authorization before scanning or querying live services.

