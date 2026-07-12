# Joff

A personal pipeline that fetches the French Journal Officiel (JO), indexes it for semantic
search, and produces LLM summaries of it in French. Code, comments, and docs are in English
(a general project convention); summary output is French because the source is French law —
see [ADR 0002](docs/adr/0002-summary-output-in-french.md).

## Language

**JO (Journal Officiel)**:
The daily publication of the French Republic containing newly enacted laws, decrees, and
appointments. Identified by publication date, or fetched as the latest published edition.
_Avoid_: JORF (used in Légifrance API field/endpoint names, but JO is the term used in
conversation and prompts)

**Text**:
A single legal document within a JO edition (a law, decree, order, etc.), identified by a
`JORFTEXT...` id from the Légifrance API. A JO edition contains many texts.
_Avoid_: document, entry, article

**Nature**:
The legal category of a text as returned by the Légifrance API (e.g. LOI, DECRET, ARRETE,
ORDONNANCE). Kept in its original French/API form rather than translated, since these are
official legal categories without a clean English equivalent.

**Chunk**:
A ~1200-character slice of a text's plain content, produced by `vectorize.py`, that gets its
own embedding and is the unit retrieved by semantic search.
_Avoid_: excerpt (used loosely in prompts/output for the same thing, but "chunk" is the
canonical term for the indexed unit)

**Global summary**:
A summary of an entire JO edition, built from just the table-of-contents titles (no vector
search involved). Produced by `summarize.py` with no topic argument.

**Thematic summary**:
A summary of a JO edition restricted to one topic, built by running semantic search for the
topic and summarizing the surviving chunks. Produced by `summarize.py "<topic>"`.

**Similarity floor**:
The minimum cosine similarity (`min_score`, default 0.83) a chunk must reach to be considered
for a thematic summary at all. Distinct from the LLM's own off-topic judgment — see
[ADR 0001](docs/adr/0001-two-tier-relevance-filtering.md).
