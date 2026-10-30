# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The ``help`` command."""
from errors import CommandError


def cmd_help(w, cmd):
    import world
    if not cmd.args:
        names = sorted(world.COMMANDS)
        w.emit("commands: " + ", ".join(names))
        return
    key = " ".join(cmd.args)
    if key not in world.COMMANDS:
        raise CommandError("unknown_command", key)
    w.emit(world.COMMANDS[key][1])
