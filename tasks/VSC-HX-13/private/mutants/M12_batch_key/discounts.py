# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The coupon registry: every coupon kind by name."""

import disc_pct_all
import disc_pct_fee
import disc_pct_usage
import disc_fixed_all
import disc_fixed_fee
import disc_fixed_usage
import disc_first_periods
import disc_volume

MODULES = {
    "pct_all": disc_pct_all,
    "pct_fee": disc_pct_fee,
    "pct_usage": disc_pct_usage,
    "fixed_all": disc_fixed_all,
    "fixed_fee": disc_fixed_fee,
    "fixed_usage": disc_fixed_usage,
    "first_periods": disc_first_periods,
    "volume": disc_volume,
}


def known(kind):
    return kind in MODULES


def get(kind):
    return MODULES[kind]


def kinds():
    return sorted(MODULES)
