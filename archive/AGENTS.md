# AGENTS.md - Repo Guide

## Purpose
GitHub Pages static site hosting articles and a UK polling dashboard (`ukcharts/`).

## Data Update Workflow (ukcharts/)
**Entry point:** `python updatedata.py`

This interactive script:
1. Backs up `ytod.csv` and `data.json` to `backup/`
2. Runs `loadwikitables.py` - scrapes Wikipedia polling tables
3. Prompts for approval before proceeding
4. Runs `process_data.py` - converts CSV to `data.json` for the dashboard

**Dependencies:** `pandas`, `requests`, `lxml` (no requirements.txt - install if missing)

**Manual alternative:**
```bash
python loadwikitables.py  # Fetches from Wikipedia, creates ytod.csv
python process_data.py    # Generates data.json from ytod.csv
```

## Architecture
- **Root:** Static HTML + `pages.json` (article listings)
- **ukcharts/:** D3 + Observable Plot dashboard consuming `data.json`
- **articles/:** Article content and code samples
- **datavizrecipes/:** Data visualization examples

## Key Files
| File | Purpose |
|------|---------|
| `ukcharts/index.html` | Dashboard UI (D3/Observable Plot) |
| `ukcharts/data.json` | Dashboard data (generated) |
| `ukcharts/ytod.csv` | Year-to-date polling data (generated) |
| `pages.json` | Article metadata for homepage |

## Gotchas
- No `requirements.txt` - dependencies are implicit
- `loadwikitables.py` creates `temp.csv` as intermediate file
- Wikipedia scraper uses `flavor='lxml'` - requires lxml installed
- Dashboard data is static - regenerate via `updatedata.py` when polls update
