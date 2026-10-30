# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""help: usage lines of the commands."""
import cmdtable
from errors import CommandError


def cmd_help(w, cmd):
    want = cmd.args[0] if cmd.args else ""
    shown = 0
    for words, usage in cmdtable.listing():
        if want and words[0] != want:
            continue
        w.out.emit(usage)
        shown += 1
    if not shown:
        raise CommandError("unknown_command", want)
