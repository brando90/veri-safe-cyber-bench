# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""``doctor``: warnings about configurations that are valid but probably
not what the operator meant.  It never changes anything."""

import localtime
import retry
import timefmt
import units


def _quiet_note(cfg, r):
    start = cfg.get("quiet.start", r)
    end = cfg.get("quiet.end", r)
    if (start is None) != (end is None):
        return "only one of quiet.start/quiet.end is set; no quiet hours apply"
    if start is not None and start == end:
        return "quiet.start equals quiet.end; no quiet hours apply"
    return None


def _quiet_minutes(cfg, r):
    window = cfg.quiet(r)
    if window is None:
        return 0
    start, end = window
    return sum(1 for m in range(units.MIN_PER_DAY) if localtime.in_window(m, start, end))


def _retry_span(cfg, r):
    """Longest time from the first attempt to the last one of a fragment."""
    total = 0
    for n in range(1, cfg.get("retry.max_attempts", r)):
        total += retry.backoff_ms(cfg, n)
    return total


def warnings(svc):
    cfg = svc.cfg
    out = []
    names = [None] + sorted(svc.recipients)
    for r in names:
        who = "global" if r is None else "recipient " + r
        if cfg.ms("ttl.default_s", r) > cfg.ms("ttl.max_s", r):
            out.append("%s: ttl.default_s above ttl.max_s; new messages get ttl.max_s" % who)
        span = _retry_span(cfg, r)
        if span >= cfg.ms("ttl.default_s", r):
            out.append("%s: retries can span %s, not less than the default TTL"
                       % (who, timefmt.fmt_seconds(span)))
        if r is None:
            continue
        note = _quiet_note(cfg, r)
        if note:
            out.append("%s: %s" % (who, note))
        if _quiet_minutes(cfg, r) >= units.MIN_PER_DAY - 60:
            out.append("%s: quiet hours cover all but less than an hour of the day" % who)
        daily = cfg.get("limit.daily", r)
        hourly = cfg.get("limit.hourly", r)
        if daily and hourly and hourly > daily:
            out.append("%s: limit.hourly above limit.daily has no effect" % who)
        vol = cfg.nbytes("limit.daily_kib", r)
        if vol and vol < cfg.nbytes("frag.size_bytes"):
            out.append("%s: daily volume smaller than one fragment" % who)
        out.extend(_recipient_state(svc, r, who))
    return out


def _recipient_state(svc, r, who):
    """Warnings about the recipient's current state rather than its config."""
    out = []
    left = svc.links.queued(r)
    if left:
        out.append("%s: %d scripted link outcome(s) not used yet" % (who, left))
    until = svc.breaker.paused_until(r)
    if until is not None and until > svc.now:
        out.append("%s: paused until %s" % (who, timefmt.fmt_instant(until)))
    stuck = [m for m in svc.messages.values()
             if m.recipient == r and m.pending and m.deadline - svc.now < units.MS_PER_MIN]
    if stuck:
        out.append("%s: %d pending message(s) expire within a minute" % (who, len(stuck)))
    return out
