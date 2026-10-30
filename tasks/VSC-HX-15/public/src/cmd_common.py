# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Helpers shared by the command handlers."""
import units
from errors import CmdError


def one_id(pos, usage):
    if len(pos) != 1:
        raise CmdError("usage: " + usage)
    return pos[0]


def only(opts, allowed, usage):
    for key in opts:
        if key not in allowed:
            raise CmdError("unknown option %s (usage: %s)" % (key, usage))


def need(opts, key):
    if key not in opts:
        raise CmdError("missing %s=" % key)
    return opts[key]


def user_range(opts):
    """Reads optional from=/to= (seconds, both ends included) as (start, end) for windows.select."""
    start = units.parse_ms(opts["from"]) if "from" in opts else 0
    if "to" in opts:
        end = units.parse_ms(opts["to"]) + 1
    else:
        end = 1 << 62
    if end <= start:
        raise CmdError("empty range")
    return start, end
