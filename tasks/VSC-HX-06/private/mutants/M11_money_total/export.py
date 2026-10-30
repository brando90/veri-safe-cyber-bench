# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""CSV exports (README, "Exports").

RFC 4180 style: fields are separated by ',' and lines end with LF.  A
field is quoted when it contains ',', '"', CR or LF, or starts or ends with
a blank; inside quotes '"' is doubled.  Message bodies are the only free
text; names, ids, numbers and instants never need quoting, but every field
goes through field() all the same.
"""

import money
import timefmt

DELIVERY_HEADER = ("id", "sender", "recipient", "prio", "size", "frags", "attempts",
                   "accepted", "finished", "body")
BILLING_HEADER = ("id", "sender", "plan", "recipient", "size", "prio", "amount", "invoice")
AUDIT_HEADER = ("n", "at", "action", "detail")

_SPECIAL = (",", '"', "\r", "\n")


def field(value):
    text = str(value)
    if any(c in text for c in _SPECIAL) or text != text.strip(" \t"):
        return '"' + text.replace('"', '""') + '"'
    return text


def row(values):
    return ",".join(field(v) for v in values)


def deliveries(svc, recipient=None):
    out = [row(DELIVERY_HEADER)]
    for m in svc.messages.values():
        if m.state != "delivered":
            continue
        if recipient is not None and m.recipient != recipient:
            continue
        attempts = sum(f.attempts for f in m.frags)
        out.append(row((m.id, m.sender, m.recipient, m.prio, m.size, len(m.frags), attempts,
                        timefmt.fmt_instant(m.accepted_at), timefmt.fmt_instant(m.finished_at),
                        m.body)))
    return out


def billing_lines(svc, sender=None):
    out = [row(BILLING_HEADER)]
    for l in svc.billing.lines:
        if sender is not None and l.sender != sender:
            continue
        out.append(row((l.msg_id, l.sender, l.plan, l.recipient, l.size, l.prio,
                        money.fmt(l.cents()), "-" if l.invoice is None else l.invoice)))
    return out


def audit_lines(svc):
    out = [row(AUDIT_HEADER)]
    for n, (at, action, detail) in enumerate(svc.audit.entries, 1):
        out.append(row((n, timefmt.fmt_instant(at), action, detail)))
    return out


KINDS = {
    "deliveries": deliveries,
    "billing": billing_lines,
    "audit": audit_lines,
}
