# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The World (output and event store) and the command table."""
import agenda
import busy
import evcmds
import events
import exporter
import helptext
import invariant
import stats
import tools
from errors import CommandError

# name: (handler, usage, options, min args, max args or None)
COMMANDS = {
    "event add": (evcmds.cmd_add,
                  "event add ID|- TITLE START [dur=D] [rule=R] [tz=OFFSET] [allday=yes] "
                  "[prio=N] [cat=LIST]",
                  ("dur", "rule", "tz", "allday", "prio", "cat"), 3, 3),
    "event show": (evcmds.cmd_show, "event show REF", (), 1, 1),
    "event rm": (evcmds.cmd_rm, "event rm REF", (), 1, 1),
    "event move": (evcmds.cmd_move, "event move REF START", (), 2, 2),
    "event rule": (evcmds.cmd_rule, "event rule REF RULE|none", (), 2, 2),
    "event retitle": (evcmds.cmd_retitle, "event retitle REF TITLE", (), 2, 2),
    "event cat": (evcmds.cmd_cat, "event cat REF LIST|-", (), 2, 2),
    "event set": (evcmds.cmd_set, "event set REF [dur=D] [tz=OFFSET] [prio=N]",
                  ("dur", "tz", "prio"), 1, 1),
    "skip": (evcmds.cmd_skip, "skip REF DATE", (), 2, 2),
    "unskip": (evcmds.cmd_unskip, "unskip REF DATE", (), 2, 2),
    "expand": (evcmds.cmd_expand, "expand REF FROM TO", (), 3, 3),
    "list": (evcmds.cmd_list, "list", (), 0, 0),
    "agenda": (agenda.cmd_agenda, "agenda FROM TO [n=N]", ("n",), 2, 2),
    "busy": (busy.cmd_busy, "busy FROM TO", (), 2, 2),
    "export text": (exporter.cmd_export_text, "export text", (), 0, 0),
    "export pack": (exporter.cmd_export_pack, "export pack", (), 0, 0),
    "import rec": (exporter.cmd_import_rec, "import rec RECORD", (), 1, 1),
    "import pack": (exporter.cmd_import_pack, "import pack SUM HEX", (), 2, 2),
    "idseq": (exporter.cmd_idseq, "idseq N", (), 1, 1),
    "ordinal": (tools.cmd_ordinal, "ordinal DATE", (), 1, 1),
    "date": (tools.cmd_date, "date N", (), 1, 1),
    "weekday": (tools.cmd_weekday, "weekday DATE", (), 1, 1),
    "shift": (tools.cmd_shift, "shift DATE N UNIT", (), 3, 3),
    "offset": (tools.cmd_offset, "offset TEXT", (), 1, 1),
    "dur": (tools.cmd_dur, "dur TEXT", (), 1, 1),
    "snap": (tools.cmd_snap, "snap START", (), 1, 1),
    "title": (tools.cmd_title, "title TEXT", (), 1, 1),
    "rule": (tools.cmd_rule, "rule TEXT", (), 1, 1),
    "ref": (tools.cmd_ref, "ref N", (), 1, 1),
    "unref": (tools.cmd_unref, "unref TEXT", (), 1, 1),
    "stats": (stats.cmd_stats, "stats", (), 0, 0),
    "check": (invariant.cmd_check, "check", (), 0, 0),
    "help": (helptext.cmd_help, "help [COMMAND]", (), 0, 2),
}


class World:
    def __init__(self, out):
        self.out = out
        self.store = events.Store()

    def emit(self, line):
        self.out.emit(line)

    def dispatch(self, cmd):
        words = cmd.words
        if len(words) >= 2 and "%s %s" % (words[0], words[1]) in COMMANDS:
            name, args = "%s %s" % (words[0], words[1]), words[2:]
        elif words[0] in COMMANDS:
            name, args = words[0], words[1:]
        else:
            raise CommandError("unknown_command", words[0])
        handler, usage, options, lo, hi = COMMANDS[name]
        for opt in sorted(cmd.opts):
            if opt not in options:
                raise CommandError("bad_option", opt, name)
        cmd.name, cmd.args, cmd.usage = name, args, usage
        if len(args) < lo or (hi is not None and len(args) > hi):
            raise CommandError("usage", usage)
        handler(self, cmd)
