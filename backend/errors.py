"""Shared exception for pipeline failures.

Library functions raise PipelineError instead of calling sys.exit, so importing
them into a long-running process (the Flask API) doesn't kill the whole server
on a single bad request. CLI entry points (main()) catch it and convert to
sys.exit(str(e)) to preserve today's command-line behavior.
"""


class PipelineError(Exception):
    def __init__(self, message, status=500):
        super().__init__(message)
        self.status = status
