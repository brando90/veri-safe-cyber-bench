# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Coupon kind volume: a volume rebate on usage, capped by the coupon percentage."""
import money

NAME = "volume"
DEFAULT_N = 0
THRESHOLDS = ((200, 15), (100, 10), (50, 5))
TARGET = 'usage'


def validate(text, exp):
    return money.parse_int(text, 1, 100)


def amount(ctx, cp):
    for need, rebate in THRESHOLDS:
        if ctx.usage >= need * 10 ** ctx.exp:
            return money.pct(ctx.usage, min(rebate, cp.value) * 100)
    return 0


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
