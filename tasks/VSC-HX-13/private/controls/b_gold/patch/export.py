# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""export: invoices, ledger or audit log as CSV or TSV rows."""
import currencies
from errors import CommandError


def field(value, fmt):
    text = str(value)
    if fmt == "tsv":
        return text.replace("\t", " ").replace("\n", " ")
    if any(c in text for c in ',"\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


def row(values, fmt):
    sep = "," if fmt == "csv" else "\t"
    return sep.join(field(v, fmt) for v in values)


def invoices(w, fmt):
    yield row(["number", "customer", "period", "issued", "due", "currency", "subtotal",
               "discount", "tax", "late", "total", "paid", "refunded"], fmt)
    for inv in w.invoices.values():
        cur = currencies.get(inv.currency)
        t = lambda amount: currencies.money_text(cur, amount)  # noqa: E731
        yield row([inv.number, inv.cust, inv.period, inv.issued, inv.due, inv.currency,
                   t(inv.subtotal), t(inv.discount), t(inv.tax), t(inv.late), t(inv.total),
                   t(inv.paid), t(inv.refunded)], fmt)


def ledger(w, fmt):
    yield row(["seq", "day", "kind", "customer", "invoice", "amount"], fmt)
    for e in w.ledger:
        cur = currencies.get(w.customers[e.cust].currency)
        yield row([e.seq, e.day, e.kind, e.cust, e.inv, currencies.money_text(cur, e.amount)], fmt)


def audit(w, fmt):
    yield row(["seq", "day", "action", "subject", "details"], fmt)
    for seq, day, action, subject, details in w.audit:
        yield row([seq, day, action, subject, " ".join(details)], fmt)


def customer_rows(w, fmt):
    yield row(["id", "name", "plan", "region", "currency", "status", "since", "terms", "po",
               "email"], fmt)
    for cid in sorted(w.customers):
        c = w.customers[cid]
        yield row([c.id, c.name, c.plan, c.region, c.currency, "closed" if c.closed else "active",
                   c.since, c.terms, c.po, c.email], fmt)


def usage_rows(w, fmt):
    yield row(["customer", "service", "units", "day", "id"], fmt)
    for rec in w.usage:
        yield row([rec.cust, rec.svc, rec.units, rec.day, rec.rid or ""], fmt)


KINDS = {"invoices": invoices, "ledger": ledger, "audit": audit, "customers": customer_rows,
         "usage": usage_rows}


def cmd_export(w, cmd):
    kind = cmd.arg(0)
    fmt = cmd.arg(1)
    if kind not in KINDS:
        raise CommandError("unknown_export", kind)
    if fmt not in ("csv", "tsv"):
        raise CommandError("unknown_format", fmt)
    for text in KINDS[kind](w, fmt):
        w.out.emit(text)
