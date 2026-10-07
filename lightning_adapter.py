"""
Lightning adapter intentionally disabled by default.

Only connect a lightning dataset after recording its exact product ID,
licence and redistribution permission in docs/SOURCES_AND_CREDITS.md.
"""

ENABLED = False

def status():
    return {
        "enabled": False,
        "reason": "No lightning source is enabled until redistribution rights are verified."
    }
