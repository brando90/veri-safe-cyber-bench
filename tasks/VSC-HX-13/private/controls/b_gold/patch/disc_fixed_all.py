# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Coupon kind fixed_all: a fixed amount off the whole subtotal."""
import money

NAME = "fixed_all"
DEFAULT_N = 0
TARGET = 'all'


def validate(text, exp):
    return money.parse(text, exp)


def amount(ctx, cp):
    return min(cp.value, ctx.subtotal)


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
