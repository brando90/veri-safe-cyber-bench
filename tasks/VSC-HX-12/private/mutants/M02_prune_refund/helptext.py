# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The help command (documentation only)."""
from errors import CommandError

INTRO = [
    "crateyard: a toy package registry",
    "commands (ACTOR acts; VIEWER reads, '-' for anonymous):",
]


def cmd_help(w, cmd):
    import world as world_mod
    table = world_mod.COMMANDS
    if cmd.args:
        name = " ".join(cmd.args)
        if name not in table:
            raise CommandError("unknown_command", name)
        w.emit("usage: %s" % table[name][1])
        return
    for line in INTRO:
        w.emit(line)
    for name in sorted(table):
        w.emit("  " + table[name][1])
