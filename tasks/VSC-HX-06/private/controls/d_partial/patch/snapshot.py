# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""``snapshot``: a deterministic dump of the whole service state.

Operators attach it to support tickets; tests use it to compare runs.
Sections appear in a fixed order and every list in it is sorted, so two
runs with the same input always print the same snapshot.
"""

import config
import localtime
import timefmt


def _config_section(svc):
    out = ["[config]"]
    for key in sorted(config.KEYS):
        src = svc.cfg.source(key)
        if src != "default":
            out.append("global %s=%s" % (key, config.render(config.KEYS[key], svc.cfg.get(key))))
    for r in sorted(svc.recipients):
        for key in sorted(config.KEYS):
            if svc.cfg.source(key, r) == "recipient":
                out.append("recipient %s %s=%s" % (
                    r, key, config.render(config.KEYS[key], svc.cfg.get(key, r))))
    return out


def _parties_section(svc):
    out = ["[parties]"]
    for name in sorted(svc.senders):
        s = svc.senders[name]
        out.append("sender %s plan=%s since=%s" % (name, s.plan, timefmt.fmt_instant(s.created_at)))
    for name in sorted(svc.recipients):
        r = svc.recipients[name]
        state = "paused" if svc.breaker.paused(name) else "active"
        out.append("recipient %s tz=%s local-day=%d state=%s scripted=%d inbox=%d" % (
            name, timefmt.fmt_offset(r.offset_min), localtime.local_day(svc.now, r.offset_min),
            state, svc.links.queued(name), len(r.inbox)))
    return out


def _messages_section(svc):
    out = ["[messages]"]
    for m in sorted(svc.messages.values(), key=lambda m: m.seq):
        acked = sum(1 for f in m.frags if f.acked)
        out.append("%s seq=%d %s %s->%s prio=%s acked=%d/%d deadline=%s" % (
            m.id, m.seq, m.state, m.sender, m.recipient, m.prio, acked, len(m.frags),
            timefmt.fmt_instant(m.deadline)))
    return out


def lines(svc):
    out = ["snapshot at %s" % timefmt.fmt_instant(svc.now)]
    out += _config_section(svc)
    out += _parties_section(svc)
    out += _messages_section(svc)
    out.append("[end]")
    return out
