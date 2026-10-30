# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The audit log.

Every state change and every request or job outcome is recorded with the
time, the tenant it concerns (``-`` when none), an event name and a list of
``name=value`` fields.  Records are numbered from 1 and never change.
Tenants and key ids are not secret and are recorded as they are; secrets
never reach the log (README.md, "Secrets").
"""
import lexer
import redact
import units
from errors import CommandError
from output import kvs


class Record:
    __slots__ = ("seq", "at", "tenant", "event", "fields")

    def __init__(self, seq, at, tenant, event, fields):
        self.seq = seq
        self.at = at
        self.tenant = tenant
        self.event = event
        self.fields = fields

    def render(self):
        text = "#%d t=%d %s %s" % (self.seq, self.at, self.tenant, self.event)
        if self.fields:
            text += " " + kvs(self.fields)
        return text


class AuditLog:
    def __init__(self, world):
        self.world = world
        self.records = []

    def record(self, tenant, event, fields):
        """Append one record.  Field values are scrubbed before they are kept."""
        clean = [(name, redact.scrub(str(value))) for name, value in fields]
        rec = Record(len(self.records) + 1, self.world.now, tenant or "-", event, clean)
        self.records.append(rec)
        return rec

    def select(self, tenant=None, event=None):
        out = []
        for rec in self.records:
            if tenant is not None and rec.tenant != tenant:
                continue
            if event is not None and rec.event != event and not rec.event.startswith(event + "."):
                continue
            out.append(rec)
        return out

    def count(self, tenant, event, result_prefix=None):
        n = 0
        for rec in self.select(tenant, event):
            if result_prefix is None:
                n += 1
                continue
            for name, value in rec.fields:
                if name == "result" and value.startswith(result_prefix):
                    n += 1
        return n


def cmd_audit(world, cmd):
    """audit [TENANT] [event=EVENT] [last=N]  |  audit export ..."""
    if len(cmd.words) >= 2 and cmd.words[1] == "export":
        import export
        export.cmd_export(world, cmd)
        return
    lexer.need(cmd, 1, 2, "audit [TENANT] [event=EVENT] [last=N]")
    lexer.allow_opts(cmd, ("event", "last"))
    tenant = None
    if len(cmd.words) == 2:
        tenant = cmd.words[1]
        if tenant != "-":
            world.tenants.require(tenant)
    last = cmd.opt("last")
    last = None if last is None else units.parse_int(last, "last", lo=1)
    records = world.audit.select(tenant, cmd.opt("event"))
    if last is not None:
        records = records[-last:]
    if not records:
        world.emit("audit none")
    for rec in records:
        world.emit(rec.render())


def cmd_check(world, cmd):
    lexer.need(cmd, 1, 1, "check")
    lexer.allow_opts(cmd, ())
    import invariant
    invariant.full_check(world)
    world.emit("check ok records=%d" % len(world.audit.records))


def unknown(name):
    raise CommandError("unknown command %s" % name)
