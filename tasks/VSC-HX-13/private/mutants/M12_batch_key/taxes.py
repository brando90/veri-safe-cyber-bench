# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The tax registry: every region module by code."""

import tax_ca
import tax_ny
import tax_tx
import tax_wa
import tax_de
import tax_fr
import tax_es
import tax_uk
import tax_jp
import tax_on
import tax_ch

MODULES = {
    "ca": tax_ca,
    "ny": tax_ny,
    "tx": tax_tx,
    "wa": tax_wa,
    "de": tax_de,
    "fr": tax_fr,
    "es": tax_es,
    "uk": tax_uk,
    "jp": tax_jp,
    "on": tax_on,
    "ch": tax_ch,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def codes():
    return sorted(MODULES)


def compute(region, lines, discount, exempt):
    return MODULES[region].compute(lines, discount, exempt)
