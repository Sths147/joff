# Summary output stays in French

All code — comments, docstrings, console/error messages — is in English, per a project-wide
convention. The LLM-generated summaries in `summarize.py`, however, are requested in French,
not English. These are separate concerns: code language is a coding convention, but the
Journal Officiel is a French legal source, and summarizing it in French avoids losing
precision on legal terms that don't translate cleanly. Don't "fix" the summary prompts back to
English to match the rest of the codebase — that was tried and reverted.
