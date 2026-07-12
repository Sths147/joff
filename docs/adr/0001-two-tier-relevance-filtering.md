# Two-tier relevance filtering for thematic summaries

`summarize.py`'s thematic mode (`summarize_theme`) filters retrieved chunks twice: a hard
similarity floor (`min_score`, default 0.83) aborts before any Mistral call if nothing in
the index clears the bar, and the system prompt separately tells Mistral that some of the
surviving top-k chunks may still be off-topic and to ignore them. These aren't redundant —
the floor exists to catch the "index has nothing on this topic at all" case cheaply, without
spending an API call or showing a summary hallucinated from garbage excerpts; the LLM
instruction exists to catch the more common case where the top-k is a mix of relevant and
irrelevant chunks that individually still clear the floor. Both stay.
