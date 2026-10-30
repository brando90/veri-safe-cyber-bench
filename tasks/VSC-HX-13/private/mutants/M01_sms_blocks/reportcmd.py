# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""report: run one of the named reports."""
import reports
from errors import CommandError


def cmd_report(w, cmd):
    name = cmd.arg(0)
    if name == "list":
        for key in reports.names():
            w.out.emit("%s %s" % (key, reports.get(key).TITLE))
        return
    if not reports.known(name):
        raise CommandError("unknown_report", name)
    w.out.emit("report %s" % name)
    reports.get(name).run(w, cmd)
    w.out.emit("end")
