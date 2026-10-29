# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Read-only reports: revenue by service, tax by rate, customer balances.

Each report prints a human-readable layout, or a TSV document when the last
argument is `tsv`.
"""

import formats
import money
import parse
import store
from errors import CommandError

USAGE = "report revenue|tax FROM TO [tsv] | report balances [tsv]"


def _range(toks):
    day_from, day_to = parse.day(toks[2]), parse.day(toks[3])
    if day_from > day_to:
        raise CommandError("bad-range: %s %s" % (day_from, day_to))
    return day_from, day_to


def revenue(rows):
    """[(service, lines, net, tax, total)] ordered by service code."""
    groups = {}
    for r in rows:
        g = groups.setdefault(r["service_code"], [0, 0, 0, 0])
        g[0] += 1
        g[1] += r["net_cents"]
        g[2] += r["tax_cents"]
        g[3] += r["total_cents"]
    return [(code,) + tuple(groups[code]) for code in sorted(groups)]


def tax_summary(rows):
    """[(tax_bp, lines, net, tax)] ordered by rate."""
    groups = {}
    for r in rows:
        g = groups.setdefault(r["tax_bp"], [0, 0, 0])
        g[0] += 1
        g[1] += r["net_cents"]
        g[2] += r["tax_cents"]
    return [(bp,) + tuple(groups[bp]) for bp in sorted(groups)]


def _totals(groups, width):
    return [sum(g[i] for g in groups) for i in range(1, width)]


def show_revenue(sess, groups, tsv):
    total = _totals(groups, 5)
    if tsv:
        rows = [[g[0], g[1]] + [money.fmt(v) for v in g[2:]] for g in groups]
        rows.append(["all", total[0]] + [money.fmt(v) for v in total[1:]])
        formats.emit_table(sess, "tsv", ("service", "lines", "net", "tax", "total"), rows)
        return
    for code, n, net, tax, gross in groups + [("all",) + tuple(total)]:
        sess.emit("%s lines=%d net=%s tax=%s total=%s"
                  % (code, n, money.fmt(net), money.fmt(tax), money.fmt(gross)))


def show_tax(sess, groups, tsv):
    total = _totals(groups, 4)
    if tsv:
        rows = [[money.fmt_rate(g[0]), g[1], money.fmt(g[2]), money.fmt(g[3])] for g in groups]
        rows.append(["all", total[0], money.fmt(total[1]), money.fmt(total[2])])
        formats.emit_table(sess, "tsv", ("rate", "lines", "net", "tax"), rows)
        return
    for bp, n, net, tax in groups:
        sess.emit("rate %s%% lines=%d net=%s tax=%s"
                  % (money.fmt_rate(bp), n, money.fmt(net), money.fmt(tax)))
    sess.emit("all lines=%d net=%s tax=%s" % (total[0], money.fmt(total[1]), money.fmt(total[2])))


def show_balances(sess, tsv):
    rows = store.balances(sess.conn)
    if tsv:
        out = [[parse.fmt_id("C", r["id"]), r["name"], money.fmt(r["invoiced"]),
                money.fmt(r["paid"]), money.fmt(r["invoiced"] - r["paid"])] for r in rows]
        formats.emit_table(sess, "tsv", ("customer", "name", "invoiced", "paid", "balance"), out)
        return
    for r in rows:
        sess.emit("%s invoiced=%s paid=%s balance=%s %s" % (
            parse.fmt_id("C", r["id"]), money.fmt(r["invoiced"]), money.fmt(r["paid"]),
            money.fmt(r["invoiced"] - r["paid"]), r["name"]))
    sess.emit("customers: %d" % len(rows))


def cmd_report(sess, line):
    toks = parse.tokens(line)
    tsv = len(toks) > 2 and toks[-1] == "tsv"
    if tsv:
        toks = toks[:-1]
    if len(toks) == 4 and toks[1] in ("revenue", "tax"):
        rows = store.lines_in_range(sess.conn, *_range(toks))
        if toks[1] == "revenue":
            show_revenue(sess, revenue(rows), tsv)
        else:
            show_tax(sess, tax_summary(rows), tsv)
    elif len(toks) == 2 and toks[1] == "balances":
        show_balances(sess, tsv)
    else:
        raise parse.usage(USAGE)
