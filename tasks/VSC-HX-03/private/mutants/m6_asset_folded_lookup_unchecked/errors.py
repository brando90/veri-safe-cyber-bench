# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exceptions shared by all sitesmith modules.

A command that cannot be carried out raises one of these; the command layer
prints ``<PREFIX>: <reason>`` and records the status of the line.
"""

OUTSIDE_TENANT = "outside tenant"
OUTSIDE_AREA = "outside area"


class SiteError(Exception):
    """Ordinary failure: printed as ``ERROR: <reason>``, line status 2."""

    status = 2
    prefix = "ERROR"

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class Denied(SiteError):
    """Safety refusal: printed as ``DENIED: <reason>``, line status 4."""

    status = 4
    prefix = "DENIED"
