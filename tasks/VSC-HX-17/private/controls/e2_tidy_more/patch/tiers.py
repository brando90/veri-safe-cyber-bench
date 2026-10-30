# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Customer tiers: backorder priority and the order value that earns free freight."""
import money
from errors import CommandError

# name: (rank, free-freight value in cents).  Rank 0 is served first.
TIERS = {
    "basic": (2, 20000),
    "silver": (1, 10000),
    "gold": (0, 5000),
}


def known(name):
    return name in TIERS


def names():
    return sorted(TIERS, key=rank)


def rank(name):
    return TIERS[name][0]


def free_at(name):
    return TIERS[name][1]


def free_freight(name, goods):
    """True if an order worth GOODS cents ships free of freight."""
    return goods >= free_at(name)


def check(name):
    if not known(name):
        raise CommandError("unknown_tier", name)
    return name


def cmd_list(w, cmd):
    for name in names():
        w.out.emit("%s rank=%d free_freight_from=%s" % (name, rank(name), money.fmt(free_at(name))))
