# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""help: the command list."""
import cmdtable


def cmd_help(w, cmd):
    topic = cmd.arg(0, "")
    for words, usage in cmdtable.listing():
        if topic and words[0] != topic:
            continue
        w.out.emit("  %s" % usage)
    w.out.emit("%d commands" % len(cmdtable.COMMANDS))
