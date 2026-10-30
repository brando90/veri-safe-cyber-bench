# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Machine-readable export of the audit log.

    audit export [TENANT] format=tsv|jsonl

TSV: a header line, then one line per record with the columns seq, t,
tenant, event, fields; inside a column a backslash is written as two
backslashes, a tab as backslash-t and a line break as backslash-n.  The
fields column is the same ``name=value`` text the plain ``audit`` command
prints.  JSONL: one JSON object per record, keys in a fixed order.

Records are exported as they are stored, already scrubbed (see audit.py),
so an export never contains more than ``audit`` shows.
"""
import json

import lexer
from errors import CommandError
from output import kvs

COLUMNS = ("seq", "t", "tenant", "event", "fields")


def tsv_cell(value):
    return (str(value).replace("\\", "\\\\").replace("\t", "\\t")
            .replace("\n", "\\n").replace("\r", "\\r"))


def tsv_lines(records):
    yield "\t".join(COLUMNS)
    for rec in records:
        cells = (rec.seq, rec.at, rec.tenant, rec.event, kvs(rec.fields))
        yield "\t".join(tsv_cell(c) for c in cells)


def jsonl_lines(records):
    for rec in records:
        obj = {"seq": rec.seq, "t": rec.at, "tenant": rec.tenant, "event": rec.event,
               "fields": {name: value for name, value in rec.fields}}
        yield json.dumps(obj, sort_keys=False, separators=(",", ":"))


def cmd_export(world, cmd):
    lexer.need(cmd, 2, 3, "audit export [TENANT] format=tsv|jsonl")
    lexer.allow_opts(cmd, ("format",))
    fmt = cmd.opt("format", "tsv")
    tenant = None
    if len(cmd.words) == 3:
        tenant = cmd.words[2]
        if tenant != "-":
            world.tenants.require(tenant)
    records = world.audit.select(tenant)
    if fmt == "tsv":
        lines = tsv_lines(records)
    elif fmt == "jsonl":
        lines = jsonl_lines(records)
    else:
        raise CommandError("audit export: format must be tsv or jsonl")
    for line in lines:
        world.emit(line)
