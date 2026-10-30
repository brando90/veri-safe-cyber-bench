# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Counters and the ``stats`` report."""

import money
import timefmt

COUNTERS = ("accepted", "rejected", "duplicates", "delivered", "failed",
            "expired", "cancelled", "attempts", "retries", "bytes")


class Stats:
    def __init__(self):
        self.c = {name: 0 for name in COUNTERS}
        self.per = {}          # recipient -> {"delivered": n, "bytes": n, "last": t}

    def bump(self, name, n=1):
        self.c[name] += n

    def recipient(self, name):
        r = self.per.get(name)
        if r is None:
            r = self.per[name] = {"delivered": 0, "bytes": 0, "last": None}
        return r

    def on_delivered(self, msg, at):
        self.bump("delivered")
        self.bump("bytes", msg.size)
        r = self.recipient(msg.recipient)
        r["delivered"] += 1
        r["bytes"] += msg.size
        r["last"] = at


def render_recipient(svc, name):
    """``stats RECIPIENT``: the recipient's line plus its current state."""
    rcpt = svc.recipients[name]
    cfg = svc.cfg
    r = svc.stats.recipient(name)
    today, volume, hour = svc.limits.summary(name, rcpt.offset_min, svc.now)
    out = ["stats %s at %s" % (name, timefmt.fmt_instant(svc.now)),
           "delivered=%d bytes=%d pending=%d" % (r["delivered"], r["bytes"], svc.pending_for(name)),
           "today=%d/%s today-bytes=%d/%s hour=%d/%s" % (
               today, _limit_text(cfg.get("limit.daily", name)),
               volume, _limit_text(cfg.nbytes("limit.daily_kib", name)),
               hour, _limit_text(cfg.get("limit.hourly", name)))]
    until = svc.breaker.paused_until(name)
    out.append("fails-in-row=%d paused=%s scripted=%d" % (
        svc.breaker.failures(name), "-" if until is None else timefmt.fmt_instant(until),
        svc.links.queued(name)))
    return out


def _limit_text(value):
    return str(value) if value else "-"


def render(svc):
    s = svc.stats.c
    pending = sum(1 for m in svc.messages.values() if m.pending)
    out = ["stats at " + timefmt.fmt_instant(svc.now),
           "accepted=%d rejected=%d duplicates=%d" % (s["accepted"], s["rejected"], s["duplicates"]),
           "delivered=%d failed=%d expired=%d cancelled=%d pending=%d" % (
               s["delivered"], s["failed"], s["expired"], s["cancelled"], pending),
           "attempts=%d retries=%d bytes=%d" % (s["attempts"], s["retries"], s["bytes"]),
           "revenue=%s" % money.fmt(money.total(svc.billing.amounts()))]
    for name in sorted(svc.recipients):
        rcpt = svc.recipients[name]
        r = svc.stats.recipient(name)
        today, volume, hour = svc.limits.summary(name, rcpt.offset_min, svc.now)
        last = "-" if r["last"] is None else timefmt.fmt_instant(r["last"])
        out.append("recipient %s delivered=%d bytes=%d today=%d today-bytes=%d hour=%d "
                   "fails-in-row=%d last=%s" % (
                       name, r["delivered"], r["bytes"], today, volume, hour,
                       svc.breaker.failures(name), last))
    return out
