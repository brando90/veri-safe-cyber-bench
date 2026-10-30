# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The currency registry: every currency module by code."""

import money

import cur_usd
import cur_eur
import cur_gbp
import cur_jpy
import cur_kwd
import cur_cad
import cur_chf
import cur_inr

MODULES = {
    "USD": cur_usd,
    "EUR": cur_eur,
    "GBP": cur_gbp,
    "JPY": cur_jpy,
    "KWD": cur_kwd,
    "CAD": cur_cad,
    "CHF": cur_chf,
    "INR": cur_inr,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def codes():
    return sorted(MODULES)


def money_text(cur, amount):
    return money.fmt(amount, cur.EXP)


def base_text(cents):
    return money.fmt(cents, 2) + " USD"
