# Python backend, TypeScript/Vue frontend, split across two Docker containers

The pipeline (fetch, vectorize, summarize) depends on `sentence-transformers` (PyTorch) for
local embeddings and is already working in Python; porting that to a TS embedding stack would
be a rewrite of working ML plumbing, not a port. The web layer instead keeps pipeline logic as
a Flask JSON API (`backend/`) and builds the page itself in Vue 3 + TypeScript (`frontend/`),
running as two Docker containers via docker-compose — separating the slow-to-rebuild
Python/PyTorch image from the frontend's fast dev loop.
