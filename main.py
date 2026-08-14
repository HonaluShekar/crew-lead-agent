"""Compatibility entry point for the Crew Lead API.

Use ``uvicorn api:app --reload`` as the primary command.  This module keeps
the documented ``uvicorn main:app --reload`` command working while ensuring
both entry points expose the same integrated API.
"""

from api import app

__all__ = ["app"]
