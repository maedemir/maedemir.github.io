# Spatial omics literature database

Living dashboard of **spatial transcriptomics** and **spatial proteomics** papers (2025-01-01 onward) for the Mirzazadeh lab.

This directory is the entire application. It is **not** part of the personal GitHub Pages site (`maedemir.github.io`). Host it as its own service. Suggested dedicated GitHub repository name: `spatial-omics-litdb`.

## What v1 does

- Discovers journals and preprints from **OpenAlex**, **PubMed**, and **bioRxiv/medRxiv**
- Resolves open-access PDFs via **Unpaywall**, publisher OA links, and preprint PDFs
- Leaves paywalled items as **metadata + access-needed** (never stores UBC/CWL/library passwords)
- Classifies papers (modality, platform, resolution, organism/tissue/system, study type)
- Serves a searchable dashboard with filters and paper pages
- Hooks **FutureHouse PaperQA2** (`paper-qa`) for corpus Q&A when `OPENAI_API_KEY` is set; otherwise Q&A degrades to keyword search over stored abstracts
- Runs as SQLite locally; the schema is Postgres-ready (`DATABASE_URL=postgresql+psycopg://...`)

## Run locally

Python 3.11+.

```bash
cd spatial-omics-litdb
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python -m spatial_omics_litdb.cli seed --reset
python -m spatial_omics_litdb.cli serve --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

- Demo seed needs **no API keys**
- Live discovery (no OpenAI key required):

```bash
python -m spatial_omics_litdb.cli ingest --preprint-days 3
```

Set `CONTACT_EMAIL` in `.env` to a lab address so OpenAlex and Unpaywall can place you in their polite pool.

## Add the OpenAI secret (PaperQA2)

Discovery works without OpenAI. Corpus Q&A and optional heavier reading need a key.

1. Create `.env` from `.env.example` (never commit `.env`).
2. Set:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

3. Install the PaperQA2 extra:

```bash
pip install -e ".[qa]"
```

4. Restart the app. The dashboard banner should switch from “waiting for OPENAI_API_KEY” to “PaperQA2 ready”.
5. Run ingest with OA PDF download enabled (default) so `data/pdfs/` fills. PaperQA2 only reads those OA files.

If the key or `paper-qa` is missing, `/ask` still answers with a labeled keyword fallback over titles/abstracts.

## Nightly ingest

On the always-on host that holds the SQLite file and `data/pdfs`:

```bash
# crontab (see deploy/crontab.example)
15 2 * * * /path/to/spatial-omics-litdb/scripts/nightly_ingest.sh >> /var/log/spatial-omics-litdb-ingest.log 2>&1
```

Equivalent systemd timer units are in `deploy/`. The job runs:

```bash
python -m spatial_omics_litdb.cli ingest --preprint-days 3
```

`--preprint-days 3` is the nightly bioRxiv/medRxiv window. First backfill (from 2025-01-01) omits that flag:

```bash
python -m spatial_omics_litdb.cli ingest
```

GitHub Actions (`.github/workflows/nightly-ingest.yml`) can **trigger** ingest on that host via `POST /api/ingest` if you set `INGEST_TOKEN` and `INGEST_WEBHOOK_URL`. Actions runners should not be the source of truth for the database.

## Deploy

Ship one web process plus the nightly job on a small VM (or Docker) with a persistent volume.

```bash
cp .env.example .env   # set CONTACT_EMAIL; add OPENAI_API_KEY when you have it
docker compose up --build -d
docker compose --profile ingest run --rm ingest   # first backfill, or use cron on the host
```

Environment:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Default `sqlite:///./data/litdb.sqlite3`. Postgres: `postgresql+psycopg://user:pass@host:5432/litdb` (install `.[postgres]`) |
| `DATA_DIR` | SQLite parent, OA PDFs, PaperQA indexes |
| `OPENAI_API_KEY` | PaperQA2; optional |
| `CONTACT_EMAIL` | OpenAlex / Unpaywall |
| `INGEST_TOKEN` | Protects `POST /api/ingest` |

Do not put this FastAPI app on GitHub Pages. Pages can keep serving the personal site; this dashboard needs a Python process and disk.

## Tests

```bash
pytest
```

## Access policy

- OA PDFs only
- Paywalled records remain searchable metadata with **Access needed**
- Licensed PDF fetching, if added later, must run on a machine the lab controls — not in this app’s secrets
