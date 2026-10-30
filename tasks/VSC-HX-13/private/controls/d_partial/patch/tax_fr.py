# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Tax region fr: French VAT."""
import money

CODE = "fr"
NAME = "French VAT"
RATE_BP = 2000
TAXABLE = frozenset(('adjust', 'fee', 'usage'))


def taxable_sum(lines):
    return sum(line.amount for line in lines if line.kind in TAXABLE)


def compute(lines, discount, exempt):
    if exempt:
        return 0
    base = taxable_sum(lines) - discount
    if base <= 0:
        return 0
    return money.pct(base, RATE_BP)


def describe():
    return "%s %d bp" % (NAME, RATE_BP)


def breakdown(lines):
    """Taxable amount per line kind, before any discount."""
    out = {}
    for line in lines:
        if line.kind in TAXABLE:
            out[line.kind] = out.get(line.kind, 0) + line.amount
    return out


def gross_to_net(total):
    """The net amount inside a tax-inclusive TOTAL."""
    return money.div_half_up(total * 10000, 10000 + RATE_BP)


def tax_inside(total):
    return total - gross_to_net(total)


def kinds_text():
    return ",".join(sorted(TAXABLE))


def rate_text():
    return money.fmt(RATE_BP, 2) + "%"


def explain(lines, discount, exempt):
    out = ["region %s %s" % (CODE, rate_text())]
    for kind, amount in sorted(breakdown(lines).items()):
        out.append("  %s %d" % (kind, amount))
    out.append("  discount %d" % discount)
    out.append("  exempt %s" % ("yes" if exempt else "no"))
    out.append("  tax %d" % compute(lines, discount, exempt))
    return out


def applies_to(kind):
    return kind in TAXABLE


def is_zero_rated():
    return RATE_BP == 0
