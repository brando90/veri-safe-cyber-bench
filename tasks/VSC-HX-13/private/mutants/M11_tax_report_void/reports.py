# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The report registry: every report module by name."""

import rpt_aging
import rpt_credits
import rpt_disc_region
import rpt_late_customer
import rpt_out_customer
import rpt_payments
import rpt_rev_period
import rpt_rev_plan
import rpt_rev_region
import rpt_tax_period
import rpt_tax_region
import rpt_top
import rpt_usage_units
import rpt_voided

MODULES = {
    "aging": rpt_aging,
    "credits": rpt_credits,
    "disc_region": rpt_disc_region,
    "late_customer": rpt_late_customer,
    "out_customer": rpt_out_customer,
    "payments": rpt_payments,
    "rev_period": rpt_rev_period,
    "rev_plan": rpt_rev_plan,
    "rev_region": rpt_rev_region,
    "tax_period": rpt_tax_period,
    "tax_region": rpt_tax_region,
    "top": rpt_top,
    "usage_units": rpt_usage_units,
    "voided": rpt_voided,
}


def known(name):
    return name in MODULES


def get(name):
    return MODULES[name]


def names():
    return sorted(MODULES)
