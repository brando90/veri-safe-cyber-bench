# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Text form of an event: thirteen ``|``-separated escaped fields.

``E|id|seq|title|start|raw|dur|rule|tz|flags|prio|cats|skips``
"""
import durations
import fields
import offsets
import rules
import timeparse
from errors import CommandError
from events import Event

NFIELDS = 13


def format_record(ev):
    cols = [
        "E", ev.id, str(ev.seq), ev.title, timeparse.format_instant(ev.start), str(ev.raw),
        durations.fmt(ev.dur), ev.rule.text() if ev.rule else "", offsets.fmt(ev.tz),
        "allday" if ev.allday else "", str(ev.prio), fields.join_list(ev.cats),
        ",".join(timeparse.format_date(d) for d in ev.skips),
    ]
    return "|".join(fields.esc(c) for c in cols)


def parse_record(line):
    try:
        cols = [fields.unesc(c) for c in line.split("|")]
        if len(cols) != NFIELDS or cols[0] != "E":
            raise ValueError("shape")
        _, eid, seq, title, start, raw, dur, rule, tz, flags, prio, cats, skips = cols
        if flags not in ("", "allday") or not seq.isdecimal() or not raw.lstrip("-").isdecimal():
            raise ValueError("flags")
        if not prio.isdecimal() or int(prio) > 9:
            raise ValueError("prio")
        return Event(eid, int(seq), title, timeparse.parse_instant(start), int(raw),
                     durations.parse(dur), rules.parse(rule) if rule else None,
                     offsets.parse(tz), flags == "allday", int(prio), fields.split_list(cats),
                     [timeparse.parse_date(d) for d in skips.split(",")] if skips else [])
    except (ValueError, CommandError):
        raise CommandError("bad_record", line) from None
