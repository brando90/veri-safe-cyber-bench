# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The category registry: every module by code."""

from errors import CommandError

import cat_fasteners
import cat_cables
import cat_paper
import cat_tools
import cat_electronics
import cat_glassware
import cat_apparel
import cat_snacks
import cat_dairy
import cat_produce
import cat_medicine
import cat_frozen
import cat_solvents
import cat_lumber

MODULES = {
    "fasteners": cat_fasteners,
    "cables": cat_cables,
    "paper": cat_paper,
    "tools": cat_tools,
    "electronics": cat_electronics,
    "glassware": cat_glassware,
    "apparel": cat_apparel,
    "snacks": cat_snacks,
    "dairy": cat_dairy,
    "produce": cat_produce,
    "medicine": cat_medicine,
    "frozen": cat_frozen,
    "solvents": cat_solvents,
    "lumber": cat_lumber,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def checked(code):
    if code not in MODULES:
        raise CommandError("unknown_category", code)
    return MODULES[code]


def codes():
    return sorted(MODULES)


def all_modules():
    return [MODULES[c] for c in sorted(MODULES)]


def groups():
    return sorted(set(cat.GROUP for cat in all_modules()))
