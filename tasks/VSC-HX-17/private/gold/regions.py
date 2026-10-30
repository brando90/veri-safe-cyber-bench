# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The region registry: every module by code."""

from errors import CommandError

import reg_arden
import reg_brook
import reg_crest
import reg_delta
import reg_ember
import reg_forge
import reg_gale
import reg_haven
import reg_depot

MODULES = {
    "arden": reg_arden,
    "brook": reg_brook,
    "crest": reg_crest,
    "delta": reg_delta,
    "ember": reg_ember,
    "forge": reg_forge,
    "gale": reg_gale,
    "haven": reg_haven,
    "depot": reg_depot,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def checked(code):
    if code not in MODULES:
        raise CommandError("unknown_region", code)
    return MODULES[code]


def codes():
    return sorted(MODULES)


def all_modules():
    return [MODULES[c] for c in sorted(MODULES)]
