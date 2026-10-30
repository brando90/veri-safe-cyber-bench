# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Audit export as TSV or CSV."""
from errors import CommandError

COLUMNS = ("seq", "time", "actor", "action", "target", "detail")


def tsv_field(value):
    text = str(value)
    return text.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


def csv_field(value):
    text = str(value)
    if text == "" or any(c in text for c in ',"\n') or text != text.strip():
        return '"' + text.replace('"', '""') + '"'
    return text


def rows(log):
    for e in log.entries:
        yield (e.seq, e.at, e.actor, e.action, e.target, e.detail_text())


def cmd_export(w, cmd):
    fmt = cmd.arg(0)
    if fmt == "tsv":
        field, sep = tsv_field, "\t"
    elif fmt == "csv":
        field, sep = csv_field, ","
    else:
        raise CommandError("bad_format", fmt)
    w.emit(sep.join(COLUMNS))
    for row in rows(w.audit):
        w.emit(sep.join(field(v) for v in row))
