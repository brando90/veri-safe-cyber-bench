# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The warehouse registry: every module by code."""

from errors import CommandError

import wh_alder
import wh_birch
import wh_cedar
import wh_dune
import wh_elm
import wh_fjord
import wh_grove
import wh_harbor
import wh_iris
import wh_juniper
import wh_kelp
import wh_larch

MODULES = {
    "alder": wh_alder,
    "birch": wh_birch,
    "cedar": wh_cedar,
    "dune": wh_dune,
    "elm": wh_elm,
    "fjord": wh_fjord,
    "grove": wh_grove,
    "harbor": wh_harbor,
    "iris": wh_iris,
    "juniper": wh_juniper,
    "kelp": wh_kelp,
    "larch": wh_larch,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def checked(code):
    if code not in MODULES:
        raise CommandError("unknown_warehouse", code)
    return MODULES[code]


def codes():
    return sorted(MODULES)


def all_modules():
    return [MODULES[c] for c in sorted(MODULES)]


def zones():
    return sorted(set(wh.ZONE for wh in all_modules()))


def accepting(group):
    return [wh for wh in all_modules() if group in wh.ACCEPTS]
