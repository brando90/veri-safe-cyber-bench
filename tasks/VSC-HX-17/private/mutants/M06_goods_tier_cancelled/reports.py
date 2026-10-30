# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The report registry: every report module by name."""

import rpt_backorders
import rpt_cancelled
import rpt_duty_region
import rpt_expiring
import rpt_freight_carrier
import rpt_freight_region
import rpt_goods_customer
import rpt_goods_region
import rpt_goods_tier
import rpt_low_stock
import rpt_returns_cat
import rpt_scrap_cat
import rpt_status
import rpt_stock_cat
import rpt_stock_wh
import rpt_value_wh

MODULES = {
    "backorders": rpt_backorders,
    "cancelled": rpt_cancelled,
    "duty_region": rpt_duty_region,
    "expiring": rpt_expiring,
    "freight_carrier": rpt_freight_carrier,
    "freight_region": rpt_freight_region,
    "goods_customer": rpt_goods_customer,
    "goods_region": rpt_goods_region,
    "goods_tier": rpt_goods_tier,
    "low_stock": rpt_low_stock,
    "returns_cat": rpt_returns_cat,
    "scrap_cat": rpt_scrap_cat,
    "status": rpt_status,
    "stock_cat": rpt_stock_cat,
    "stock_wh": rpt_stock_wh,
    "value_wh": rpt_value_wh,
}


def known(name):
    return name in MODULES


def get(name):
    return MODULES[name]


def names():
    return sorted(MODULES)
