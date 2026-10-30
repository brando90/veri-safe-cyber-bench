# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Coupon kind pct_fee: a percentage off the plan fee lines."""
import money

NAME = "pct_fee"
DEFAULT_N = 0
TARGET = 'fee'


def validate(text, exp):
    return money.parse_int(text, 1, 100)


def amount(ctx, cp):
    return money.pct(ctx.fee, cp.value * 100)


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
