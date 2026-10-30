# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Exit codes and the exception types shared by the command layer."""

EXIT_OK = 0
EXIT_INVARIANT = 86


class CommandError(Exception):
    """A refused command; the message is printed as 'error: MESSAGE'."""


class Rejected(Exception):
    """A log line that was not stored; printed as 'rejected: REASON'."""


class InvariantViolation(Exception):
    """The self-check found the program state inconsistent."""


USAGE = {
    "now": "now TIMESTAMP",
    "retain": "retain DAYS",
    "window": "window SECONDS",
    "limit": "limit SOURCE|* COUNT",
    "top": "top COUNT",
    "salt": "salt TEXT",
    "strict": "strict on|off",
    "rule": "rule ACTION NAME | rule prefix PREFIX [ACTION]",
    "unrule": "unrule NAME",
    "log": "log TIMESTAMP SOURCE USER [NAME=VALUE ...] [-- MESSAGE]",
    "export": "export [SOURCE] [keep=NAME,NAME]",
    "show": "show ID",
}


def usage(cmd):
    return CommandError("usage: %s" % USAGE[cmd])
