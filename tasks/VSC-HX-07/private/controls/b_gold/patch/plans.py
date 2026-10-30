# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Built-in defaults and the three subscription plans.

The default layer of the configuration starts as BASE; every plan has its
own layer ``plan:NAME`` that starts as the plan's overrides.  All values are
written in the same text form a ``config set`` command would use.
"""

BASE = {
    "rate.mode": "fixed",
    "rate.limit": "10",
    "rate.window": "10s",
    "quota.requests": "1000",
    "quota.egress": "1MiB",
    "quota.period": "1d",
    "cache.ttl": "30s",
    "cache.capacity": "256KiB",
    "replay.window": "5m",
    "replay.skew": "30s",
    "replay.required": "off",
    "jobs.max_attempts": "3",
    "jobs.backoff": "1s",
    "price.request": "1500",
    "price.kib": "400",
    "backend.token": "",
    "webhook.url": "",
    "webhook.secret": "",
}


class Plan:
    def __init__(self, name, title, overrides):
        self.name = name
        self.title = title
        self.overrides = dict(overrides)


PLANS = {
    "free": Plan("free", "Free", {
        "rate.limit": "5",
        "quota.requests": "200",
        "quota.egress": "64KiB",
        "price.request": "2000",
        "price.kib": "500",
    }),
    "basic": Plan("basic", "Basic", {
        "rate.limit": "20",
        "quota.requests": "5000",
        "quota.egress": "1MiB",
    }),
    "pro": Plan("pro", "Pro", {
        "rate.mode": "sliding",
        "rate.limit": "50",
        "rate.window": "1m",
        "quota.requests": "100000",
        "quota.egress": "64MiB",
        "cache.ttl": "2m",
        "price.request": "1000",
        "price.kib": "250",
    }),
}

DEFAULT_PLAN = "free"


def names():
    return sorted(PLANS)


def cmd_plan(world, cmd):
    import lexer
    lexer.need(cmd, 2, 2, "plan list")
    lexer.allow_opts(cmd, ())
    if cmd.words[1] != "list":
        from errors import CommandError
        raise CommandError("plan: unknown subcommand %s" % cmd.words[1])
    for name in names():
        plan = PLANS[name]
        tenants = sum(1 for t in world.tenants.all() if t.plan == name)
        world.emit("plan %s title=%s tenants=%d" % (name, plan.title, tenants))
