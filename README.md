# joff

A personal summarizer of the French Journal Officiel (JO): fetches the latest official law
publications, indexes them for semantic search, and produces LLM summaries in French.

## What it does

- Fetches the daily JO (the French law gazette) via the Légifrance API
- Indexes texts for semantic search (local embeddings, no external vector DB)
- Summarizes JO editions with an LLM (Mistral), globally or filtered to a topic
- Personalizes summaries per user profile
- Runs as a multi-user web app (login required), or as standalone CLI scripts

## Layout

- `backend/` — the pipeline (fetch, vectorize, summarize) and the Flask JSON API, in Python.
- `frontend/` — the web page, in Vue 3 + TypeScript.
- `data/` — fetched JO texts and the vector index, shared by both CLI and web use. Not committed.

## Starting the server

```bash
cp backend/.env.example backend/.env
# fill in PISTE_CLIENT_ID/SECRET, MISTRAL_API_KEY, and generate the three auth secrets:
#   POSTGRES_PASSWORD, JWT_SECRET, CRON_TOKEN (openssl rand -hex 32 for the latter two)
docker compose up --build
```

For local development with hot reload, instead run just the databases in Docker and the app
directly on the host:

```bash
docker compose up mongo postgres

cd backend
export $(grep -v '^#' .env | xargs)   # backend reads config from the environment, not .env directly
flask --app app run --port 5001

# in a second terminal
cd frontend
npm run dev
```

## Accessing it

- Docker: https://localhost (self-signed certificate — accept the browser warning to continue)
- Local dev: http://localhost:5173

Register an account on first visit — every route requires being logged in. Each user gets their
own profile ("Profile" tab) for personalized summaries; the JO data itself (fetched texts, vector
index) is shared across all accounts.

`data/`, the model cache, accounts, and profiles persist across rebuilds in Docker volumes.
`JWT_SECRET` must be set in `backend/.env` in both setups, or login/register will fail.

See `docs/adr/` for the reasoning behind these setups.

## CLI tools

### Fetching the JO via the Légifrance API (PISTE)

`backend/dl_journal.py` fetches the table of contents of the Journal Officiel (JORF) via the
Légifrance API on PISTE (production by default, `PISTE_ENV=sandbox` for the test environment).

Prerequisites:

1. An account on [piste.gouv.fr](https://piste.gouv.fr) with an application subscribed to the **Légifrance** API.
2. Copy `backend/.env.example` to `backend/.env` and fill in the application's `client_id` / `client_secret`.
3. Python 3 with `requests` (`pip install requests`), or `pip install -r backend/requirements.txt` for everything (Flask, sentence-transformers, pytest included).

```bash
cd backend
python3 dl_journal.py              # today's JO
python3 dl_journal.py 2026-07-01   # JO for a given date
python3 dl_journal.py --last       # latest published JO
```

The script:
1. obtains an OAuth2 token (client credentials) from `oauth.piste.gouv.fr`;
2. calls `POST /consult/jorfCont` (by date) or `POST /consult/lastNJo` then `jorfCont` (by id) on `api.piste.gouv.fr/dila/legifrance/lf-engine-app`;
3. prints the list of texts in the table of contents (title, nature, `JORFTEXT...` id) and saves the raw response to `jo_raw.json`.

Note: the JO is not published every day — if today's date returns nothing, use `--last`.

### Fetching the full text and semantic search

Additional prerequisite: `pip install sentence-transformers` (installs PyTorch, ~2 GB; the embedding model `intfloat/multilingual-e5-small`, ~470 MB, is downloaded on first run).

```bash
cd backend
python3 fetch_texts.py             # full text of today's JO texts → ../data/<date>/
python3 fetch_texts.py --last      # or of the latest published JO
python3 vectorize.py               # chunk + vectorize all of data/ → ../data/index/
python3 search.py "price of reimbursed medicines"   # semantic search (top 5)
```

- `fetch_texts.py` calls `POST /consult/jorf` with each `textCid` from the table of contents and extracts the plain text from the HTML.
- `vectorize.py` splits each text into chunks (~1200 characters), vectorizes them locally, and stores the index (numpy + jsonl) in `data/index/`.
- `search.py` vectorizes the query and returns the closest chunks (cosine similarity).

### LLM summary (Mistral API, free)

Prerequisite: a Mistral API key (free "Experiment" plan) created on [console.mistral.ai](https://console.mistral.ai), to be put in `backend/.env` (`MISTRAL_API_KEY=...`).

```bash
cd backend
python3 summarize.py             # global thematic summary of the latest downloaded JO
python3 summarize.py "health"    # targeted summary: vector search then summary of the excerpts
```

- Without an argument: sends the table-of-contents titles to Mistral for a global summary by theme.
- With a topic: selects the closest chunks in the index (`-k N`, default 10) and asks Mistral to summarize them while citing the `JORFTEXT...` identifiers — it is the LLM that discards off-topic excerpts returned by the vector search.
- Default model: `mistral-small-latest` (changeable via `MISTRAL_MODEL` in `backend/.env`).

## Tests

```bash
cd backend
python3 -m pytest tests/
```
