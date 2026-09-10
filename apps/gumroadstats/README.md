# Gumroad Dashboard — PyScript edition

Static, serverless port of the Flask app in `..`. Runs entirely in the
browser via [PyScript](https://pyscript.net) (Pyodide + pandas + plotly).

## Run

Serve over HTTP (required — WASM + `fetch` do not work on `file://`):

```bash
cd pyscript
python3 -m http.server 8000
# open http://127.0.0.1:8000
```

First load takes ~5–10s (Python runtime + packages). After that all
filtering, charts and CSV download happen locally.

## Files

- `index.html` — static Bootstrap shell (replaces Jinja template).
- `main.py` — dashboard logic, ported from `../dashboard/data.py`.
- `pyscript.toml` — package list (`pandas`, `plotly`) + `[[fetch]]` for `sales.csv`.
- `sales.csv` — copy of the default dataset bundled for static hosting.

## Flask → PyScript mapping

| Flask | PyScript |
|---|---|
| `GET /?applied=…` + Jinja | DOM filter widgets + `render()` in `main.py` |
| `session["upload_id"]` + `instance/uploads/` | in-memory `BASE` DataFrame |
| `POST /upload` | File API → `arrayBuffer()` → `pd.read_csv(BytesIO)` |
| `POST /use-default` | re-read bundled `sales.csv` |
| `GET /download` | `Blob` download via `window.downloadCSV` |
| `fig.to_html()` server-side | `plotly.io.to_json` + `Plotly.react` (scripts in `innerHTML` don't execute) |

## Limitations vs Flask

- No multi-user sessions or server persistence; one dataset per tab.
- Cold start downloads ~20MB of WASM packages.
- Very large CSVs (>10MB) will be slow in WASM.
