# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Stand-alone conversion commands (no event involved)."""
import civil
import durations
import fields
import ids
import offsets
import rules
import shifts
import timeparse
from errors import CommandError
from output import quote


def parse_int(text):
    body = text[1:] if text[:1] in "+-" else text
    if not body.isdigit() or len(body) > 12:
        raise CommandError("bad_number", text)
    return int(text)


def cmd_ordinal(w, cmd):
    w.emit(str(timeparse.parse_date(cmd.arg(0))))


def cmd_date(w, cmd):
    z = parse_int(cmd.arg(0))
    if not civil.in_range(z):
        raise CommandError("out_of_range")
    w.emit("%s %s" % (timeparse.format_date(z), civil.weekday_name(z)))


def cmd_weekday(w, cmd):
    w.emit(civil.weekday_name(timeparse.parse_date(cmd.arg(0))))


def cmd_shift(w, cmd):
    day = timeparse.parse_date(cmd.arg(0))
    out = shifts.shift(day, parse_int(cmd.arg(1)), cmd.arg(2))
    w.emit(timeparse.format_date(out))


def cmd_offset(w, cmd):
    minutes = offsets.parse(cmd.arg(0))
    w.emit("%s %d" % (offsets.fmt(minutes), minutes))


def cmd_dur(w, cmd):
    seconds = durations.parse(cmd.arg(0))
    w.emit("%d %s" % (seconds, durations.fmt(seconds)))


def cmd_snap(w, cmd):
    start, raw = timeparse.parse_start(cmd.arg(0), False)
    w.emit("%s given %s" % (timeparse.format_instant(start), timeparse.format_exact(raw)))


def cmd_title(w, cmd):
    w.emit(quote(fields.clean_title(cmd.arg(0))))


def cmd_rule(w, cmd):
    w.emit(rules.parse(cmd.arg(0)).text())


def cmd_ref(w, cmd):
    n = parse_int(cmd.arg(0))
    if not 0 <= n <= ids.MAX_SEQ:
        raise CommandError("bad_number", cmd.arg(0))
    w.emit(ids.encode(n))


def cmd_unref(w, cmd):
    try:
        w.emit(str(ids.decode(cmd.arg(0))))
    except ValueError:
        raise CommandError("bad_ref", cmd.arg(0)) from None
