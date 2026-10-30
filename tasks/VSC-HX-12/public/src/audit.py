# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The audit log of every accepted change."""
import output
import policy
import units


class Entry:
    __slots__ = ("seq", "at", "actor", "action", "target", "detail")

    def __init__(self, seq, at, actor, action, target, detail):
        self.seq = seq
        self.at = at
        self.actor = actor
        self.action = action
        self.target = target
        self.detail = detail

    def detail_text(self):
        return " ".join(output.kv(k, v) for k, v in self.detail)


class AuditLog:
    def __init__(self, world):
        self.world = world
        self.entries = []

    def record(self, actor, action, target, detail=()):
        e = Entry(len(self.entries) + 1, self.world.now, actor, action, target, list(detail))
        self.entries.append(e)
        return e


def line(e):
    text = "#%d t=%d %s %s %s" % (e.seq, e.at, e.actor, e.action, e.target)
    extra = e.detail_text()
    return text + (" " + extra if extra else "")


def cmd_audit(w, cmd):
    n = units.parse_kib(cmd.opt("n", str(policy.AUDIT_DEFAULT)))
    entries = w.audit.entries[-n:] if n else []
    if not entries:
        w.emit("audit: empty")
        return
    for e in entries:
        w.emit(line(e))
