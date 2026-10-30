# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Command handlers.  Each takes (world, rest) and prints through world.out."""
import invariant
import names
import redact
import reports
import stamp
from errors import CommandError, Rejected, usage
from policy import ACTIONS, RULE_WORDS
from records import parse_log


def number(text, low=0):
    if not (text.isascii() and text.isdigit()) or int(text) < low:
        raise CommandError("bad number %s" % text)
    return int(text)


def c_now(world, rest):
    if len(rest.split()) != 1:
        raise usage("now")
    when = stamp.parse(rest.strip())
    if when is None:
        raise CommandError("bad timestamp %s" % rest.strip())
    world.now = when
    world.out.emit("clock set to %s" % stamp.fmt(when))


def c_retain(world, rest):
    if len(rest.split()) != 1:
        raise usage("retain")
    world.retain = number(rest.strip())
    world.out.emit("retention set to %d days" % world.retain)


def c_window(world, rest):
    if len(rest.split()) != 1:
        raise usage("window")
    world.window = number(rest.strip(), 1)
    world.out.emit("window set to %d seconds" % world.window)


def c_limit(world, rest):
    words = rest.split()
    if len(words) != 2:
        raise usage("limit")
    count = number(words[1])
    if words[0] == "*":
        world.default_limit = count
        world.out.emit("default limit set to %d" % count)
    else:
        world.limits[words[0].lower()] = count
        world.out.emit("limit for %s set to %d" % (words[0].lower(), count))


def c_top(world, rest):
    if len(rest.split()) != 1:
        raise usage("top")
    world.top = number(rest.strip(), 1)
    world.out.emit("top set to %d" % world.top)


def c_salt(world, rest):
    if not rest.strip():
        raise usage("salt")
    world.policy.salt = rest.strip()
    world.out.emit("salt set")


def c_strict(world, rest):
    word = rest.strip()
    if word not in ("on", "off"):
        raise usage("strict")
    world.policy.strict = word == "on"
    world.out.emit("strict mode %s" % word)


def c_rule(world, rest):
    words = rest.split()
    if len(words) < 2:
        raise usage("rule")
    if words[0] == "prefix":
        if len(words) > 3:
            raise usage("rule")
        world.policy.add_prefix(words[1], *words[2:])
        world.out.emit("rule added: prefix %s" % names.base(words[1]))
        return
    if len(words) != 2:
        raise usage("rule")
    world.policy.add_rule(words[0], words[1])
    world.out.emit("rule added: %s %s" % (words[0], names.base(words[1])))


def c_unrule(world, rest):
    if len(rest.split()) != 1:
        raise usage("unrule")
    if not world.policy.remove(rest.strip()):
        raise CommandError("no rule for %s" % names.base(rest.strip()))
    world.out.emit("rules removed for %s" % names.base(rest.strip()))


def c_log(world, rest):
    if not rest.strip():
        raise usage("log")
    store = world.store
    try:
        record = parse_log(rest, store.next_id)
    except Rejected as exc:
        world.out.emit("rejected: %s" % exc)
        return
    store.new_id()
    store.add(record)
    world.out.emit("logged #%d" % record.id)


def c_purge(world, rest):
    removed = world.store.purge(world.now, world.retain)
    kept = len(world.store.records)
    if removed:
        world.out.emit("purged %d records (ids %s), %d kept" % (
            len(removed), ", ".join(str(r) for r in removed), kept))
    else:
        world.out.emit("purged 0 records, %d kept" % kept)


def emit_record(world, record, policy=None):
    view, changed = redact.apply(record, policy or world.policy)
    world.out.emit(redact.line(view))
    if changed:
        world.out.emit("    changed: %s" % ", ".join(changed))
    return len(changed)


def c_export(world, rest):
    extra, words = [], []
    for word in rest.split():
        if word.startswith("keep="):
            extra.extend(n for n in word[5:].split(",") if n)
        else:
            words.append(word)
    if len(words) > 1:
        raise usage("export")
    source = words[0].lower() if words else ""
    policy = world.policy.temporary(extra) if extra else world.policy
    count = fields = 0
    for record in world.store.records:
        if source and record.source != source:
            continue
        fields += emit_record(world, record, policy)
        count += 1
    world.out.emit("exported %d records, %d fields changed" % (count, fields))


def c_show(world, rest):
    if len(rest.split()) != 1:
        raise usage("show")
    rid = number(names.clean_id(rest.strip()), 1)
    record = world.store.get(rid)
    if record is None:
        raise CommandError("no record #%d" % rid)
    emit_record(world, record)


def c_report(world, rest):
    for line in reports.build(world):
        world.out.emit(line)


def c_days(world, rest):
    for line in reports.days(world):
        world.out.emit(line)


def c_stats(world, rest):
    for line in reports.field_stats(world):
        world.out.emit(line)


def c_rules(world, rest):
    policy = world.policy
    lines = []
    for action in ACTIONS:
        if policy.named[action]:
            lines.append("%s: %s" % (action, " ".join(sorted(policy.named[action]))))
    if policy.keep:
        lines.append("keep: %s" % " ".join(sorted(policy.keep)))
    for prefix, action in policy.prefixes:
        lines.append("prefix %s: %s" % (prefix, action))
    lines.append("strict: %s" % ("on" if policy.strict else "off"))
    for line in lines:
        world.out.emit(line)


def c_check(world, rest):
    invariant.check(world)
    world.out.emit("check ok")


def c_help(world, rest):
    world.out.emit("commands: " + " ".join(sorted(COMMANDS)))
    world.out.emit("rule actions: " + " ".join(RULE_WORDS))


def old_rule_summary(world):
    return ", ".join(a for a in ACTIONS if world.policy.named[a])


COMMANDS = {
    "now": c_now, "retain": c_retain, "window": c_window, "limit": c_limit,
    "top": c_top, "salt": c_salt, "strict": c_strict, "rule": c_rule,
    "unrule": c_unrule, "log": c_log, "purge": c_purge, "export": c_export,
    "show": c_show, "report": c_report, "check": c_check, "help": c_help,
    "days": c_days, "stats": c_stats, "rules": c_rules,
}
