# Open questions

Known limitations or design shortcuts, accepted for now, worth revisiting if their
assumptions stop holding.

## vectorize.py rebuilds the whole index every run

`vectorize.py` recomputes embeddings for every chunk under `data/` on every run, including
texts already embedded in a previous run — there's no incremental indexing. Fine at personal
scale (local embedding model, a handful of JO editions). Revisit with incremental indexing
(skip chunks already in `chunks.jsonl`) if `data/` grows enough that full recompute becomes
slow.

## Chunk size/overlap are untested placeholders

`CHUNK_SIZE=1200` / `CHUNK_OVERLAP=200` in `vectorize.py` were picked as reasonable-sounding
defaults, not validated against retrieval quality on real JO texts. Worth spot-checking with
`search.py` against known topics before trusting them.
