# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The plan table: monthly fee in base units (US cents) per billing period."""
import currencies
import services
from errors import CommandError

FEES = {
    "free": 0,
    "starter": 1900,
    "team": 7900,
    "business": 19900,
    "enterprise": 59900,
}
ORDER = ("free", "starter", "team", "business", "enterprise")


def known(name):
    return name in FEES


def fee(name):
    return FEES[name]


def cmd_list(w, cmd):
    for name in ORDER:
        w.out.emit("%s fee=%s" % (name, currencies.base_text(FEES[name])))


def cmd_show(w, cmd):
    name = cmd.arg(0)
    if not known(name):
        raise CommandError("unknown_plan", name)
    w.out.emit("plan %s fee=%s" % (name, currencies.base_text(FEES[name])))
    for code in services.codes():
        svc = services.get(code)
        w.out.emit("  allowance %s %d %s" % (code, svc.ALLOW[name], svc.UNIT))
