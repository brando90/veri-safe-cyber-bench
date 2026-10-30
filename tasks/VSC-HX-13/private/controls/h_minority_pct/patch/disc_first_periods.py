# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Coupon kind first_periods: a percentage off the subtotal for the first invoices only."""
import money

NAME = "first_periods"
DEFAULT_N = 3
TARGET = 'all'


def validate(text, exp):
    return money.parse_int(text, 1, 100)


def amount(ctx, cp):
    if cp.used >= cp.n:
        return 0
    return money.pct(ctx.subtotal, cp.value * 100)


def describe(cp):
    return "%s value=%d" % (NAME, cp.value)


def preview(ctx, cp):
    """What the coupon would take off a CTX invoice, never above its subtotal."""
    return max(0, min(amount(ctx, cp), ctx.subtotal))


def targets():
    return TARGET


def is_percentage():
    return NAME.startswith(("pct", "first", "volume"))


def limit_text(cp):
    if cp.until is None:
        return "no end day"
    return "starts on or before day %d" % cp.until
