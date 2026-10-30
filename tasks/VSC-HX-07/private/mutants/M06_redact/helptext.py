# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Built-in help.

    help                    one line per command
    help COMMAND            the usage lines of one command
    help setting NAME       what a setting means, its range and built-in values

The texts here are documentation only; nothing in the program reads them to
decide anything.  Ranges are taken from the configuration schema so that the
two never disagree.
"""
import config
import lexer
import plans
import redact
import units
from errors import CommandError
from output import kv

USAGE = {
    "clock": ("clock", "clock set TIME", "clock advance DURATION"),
    "tenant": ("tenant add NAME [plan=PLAN]", "tenant plan NAME PLAN",
               "tenant suspend NAME", "tenant resume NAME", "tenant list"),
    "plan": ("plan list",),
    "config": ("config set LAYER NAME VALUE", "config load LAYER NAME=VALUE ...",
               "config unset LAYER NAME", "config get TENANT NAME", "config show TENANT",
               "config explain TENANT NAME", "config layers"),
    "key": ("key issue TENANT KEYID secret=SECRET [ttl=DURATION] [label=TEXT]",
            "key revoke TENANT KEYID", "key rotate TENANT KEYID secret=SECRET",
            "key list TENANT", "key show TENANT KEYID"),
    "req": ("req CRED METHOD PATH [nonce=N ts=S] [q.NAME=VALUE ...]",),
    "job": ("job submit CRED PATH [delay=DURATION] [prio=N] [q.NAME=VALUE ...]",
            "job cancel ID"),
    "jobs": ("jobs run", "jobs list"),
    "cache": ("cache stats", "cache list", "cache purge TENANT"),
    "usage": ("usage TENANT",),
    "top": ("top",),
    "bill": ("bill [TENANT]",),
    "stats": ("stats",),
    "audit": ("audit [TENANT] [event=EVENT] [last=N]",
              "audit export [TENANT] format=tsv|jsonl"),
    "report": ("report denials", "report tenant TENANT"),
    "webhook": ("webhook list TENANT", "webhook clear TENANT"),
    "nonce": ("nonce list TENANT KEYID",),
    "rate": ("rate show TENANT",),
    "quota": ("quota reset TENANT",),
    "check": ("check",),
    "help": ("help", "help COMMAND", "help setting NAME"),
}

SUMMARY = {
    "clock": "show or move the logical clock",
    "tenant": "create, re-plan, suspend and list tenants",
    "plan": "list the subscription plans",
    "config": "change and inspect layered settings",
    "key": "issue, revoke, rotate and list API keys",
    "req": "send one request through the gateway",
    "job": "queue or cancel one background job",
    "jobs": "run due jobs, list the queue",
    "cache": "inspect or purge the response cache",
    "usage": "a tenant's quota, rate window and meter",
    "top": "tenants by accepted requests",
    "bill": "the bill of one or every tenant",
    "stats": "global counters",
    "audit": "show or export the audit log",
    "report": "denial and per-tenant reports",
    "webhook": "deliveries waiting in the outbox",
    "nonce": "nonces remembered for a key",
    "rate": "the rate window of a tenant",
    "quota": "start a tenant's quota period afresh",
    "check": "run the consistency check",
    "help": "this text",
}

MEANING = {
    "rate.mode": "fixed: windows start at multiples of rate.window; "
                 "sliding: the window ends at the current time",
    "rate.limit": "accepted requests per window; 0 refuses every request",
    "rate.window": "length of the rate window",
    "quota.requests": "accepted requests and jobs per quota period",
    "quota.egress": "response bytes per quota period",
    "quota.period": "length of a quota period; periods start at multiples of it",
    "cache.ttl": "how long a cached response may be served; 0 disables caching",
    "cache.capacity": "total size of the response cache (global)",
    "replay.window": "how long a used nonce is remembered",
    "replay.skew": "largest allowed distance between ts and the current time",
    "replay.required": "when on, every request must carry nonce= and ts=",
    "jobs.max_attempts": "attempts before a job is given up",
    "jobs.backoff": "delay before the first retry; doubled for each later one",
    "price.request": "price of one accepted request or job, in millicents",
    "price.kib": "price of one KiB of egress, in millicents",
    "backend.token": "credential the gateway presents upstream",
    "webhook.url": "where job completions are delivered",
    "webhook.secret": "key used to sign webhook deliveries",
}


def _bound(setting, value):
    if value is None:
        return "-"
    if setting.kind == "duration":
        return units.fmt_duration(value)
    if setting.kind == "size":
        return units.fmt_size(value)
    return str(value)


def _builtin(name):
    """Built-in default and plan values (as shipped, not as configured now)."""
    out = [("default", plans.BASE.get(name, ""))]
    for pname in plans.names():
        over = plans.PLANS[pname].overrides
        if name in over:
            out.append((pname, over[name]))
    return out


def describe_setting(world, name):
    setting = config.SCHEMA.get(name)
    if setting is None:
        raise CommandError("help: unknown setting %s" % name)
    world.emit("setting %s kind=%s scope=%s sensitive=%s" % (
        name, setting.kind, setting.scope, "yes" if redact.is_sensitive(name) else "no"))
    if setting.kind in ("int", "duration", "size"):
        world.emit("  range %s..%s" % (_bound(setting, setting.lo), _bound(setting, setting.hi)))
    elif setting.kind == "choice":
        world.emit("  choices %s" % " ".join(setting.choices))
    elif setting.kind == "flag":
        world.emit("  choices on off")
    else:
        world.emit("  text of at most 128 printable characters")
    for where, value in _builtin(name):
        world.emit("  built-in %s %s" % (where, kv("value", redact.show_value(name, value))))
    world.emit("  %s" % MEANING.get(name, "-"))


def list_commands(world):
    for name in sorted(USAGE):
        world.emit("%-8s %s" % (name, SUMMARY.get(name, "")))


def show_command(world, name):
    lines = USAGE.get(name)
    if lines is None:
        raise CommandError("help: unknown command %s" % name)
    for line in lines:
        world.emit("usage: %s" % line)


def cmd_help(world, cmd):
    lexer.need(cmd, 1, 3, "help [COMMAND] | help setting NAME")
    lexer.allow_opts(cmd, ())
    words = cmd.words
    if len(words) == 1:
        list_commands(world)
    elif words[1] == "setting":
        if len(words) != 3:
            raise CommandError("usage: help setting NAME")
        describe_setting(world, words[2])
    elif len(words) == 2:
        show_command(world, words[1])
    else:
        raise CommandError("usage: help [COMMAND] | help setting NAME")
