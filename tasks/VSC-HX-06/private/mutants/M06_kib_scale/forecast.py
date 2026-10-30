# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""``forecast RECIPIENT SIZE``: earliest instant a new message could start.

Only the recipient's limits are considered (daily count, rolling hour,
daily volume); quiet hours, pauses and the queue are ignored.  The
forecast is read-only: it works on a copy of the recorded starts and never
prunes the ledger's rolling window, so asking about a future instant does
not change what the dispatcher sees now.

Limits can only lift at a local midnight or when a start leaves the rolling
hour, so those are the only instants that need to be tried.
"""

import localtime
import timefmt
import timewin
import units

HORIZON_MS = 2 * units.MS_PER_DAY


def _starts(svc, recipient):
    return list(svc.limits._starts.get(recipient, ()))


def reason_at(svc, recipient, starts, t, size):
    """The limit that blocks a start of SIZE bytes at T, or None."""
    cfg = svc.cfg
    offset = svc.offset_of(recipient)
    day = localtime.local_day(t, offset)
    today = [s for s in starts if s[2] == day]
    daily = cfg.get("limit.daily", recipient)
    if daily and len(today) >= daily:
        return "daily"
    hourly = cfg.get("limit.hourly", recipient)
    if hourly:
        recent = sum(1 for at, _, _ in starts
                     if at <= t and timewin.within(at, t, units.MS_PER_HOUR))
        if recent >= hourly:
            return "hourly"
    cap = cfg.nbytes("limit.daily_kib", recipient)
    if cap and sum(s[1] for s in today) + size > cap:
        return "volume"
    return None


def candidates(svc, recipient, starts, now):
    offset = svc.offset_of(recipient)
    out = {now}
    t = now
    while t <= now + HORIZON_MS:
        t = localtime.next_local_midnight(t, offset)
        out.add(t)
    for at, _, _ in starts:
        leave = timewin.leaves_at(at, units.MS_PER_HOUR)
        if leave > now:
            out.add(leave)
    return sorted(c for c in out if c <= now + HORIZON_MS)


def lines(svc, recipient, size):
    now = svc.now
    starts = _starts(svc, recipient)
    head = "forecast %s size=%d at %s" % (recipient, size, timefmt.fmt_instant(now))
    cap = svc.cfg.nbytes("limit.daily_kib", recipient)
    if cap and size > cap:
        return [head, "never: larger than the daily volume of %d bytes" % cap]
    first = reason_at(svc, recipient, starts, now, size)
    if first is None:
        return [head, "can start now"]
    for t in candidates(svc, recipient, starts, now):
        if reason_at(svc, recipient, starts, t, size) is None:
            return [head, "blocked by %s; earliest start %s" % (first, timefmt.fmt_instant(t))]
    return [head, "blocked by %s beyond %s" % (first, timefmt.fmt_instant(now + HORIZON_MS))]
