# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Error type for rejected commands."""


class CmdError(Exception):
    """A rejected command; the message is printed as 'error: MESSAGE'."""
