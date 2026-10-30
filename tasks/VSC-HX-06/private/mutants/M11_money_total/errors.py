# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exception types shared by every relaydesk module."""


class CommandError(Exception):
    """A command line was refused.  The dispatcher prints
    ``ERROR <command>: <message>`` and continues with the next line."""


class InvariantError(Exception):
    """A documented invariant does not hold.  This is always a program bug:
    main.py prints ``INVARIANT: <message>`` on stderr and exits with 86."""


EXIT_INVARIANT = 86
