#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""logveil: a toy audit-log redaction and retention tool.

Reads commands from standard input, one per line, and prints results on
standard output.  See README.md for the command set.
"""
import io
import sys

import invariant
from cmds import COMMANDS
from errors import EXIT_INVARIANT, EXIT_OK, CommandError, InvariantViolation
from store import World


class Output:
    def __init__(self, stream):
        self.stream = stream

    def emit(self, line):
        self.stream.write(line + "\n")

    def flush(self):
        self.stream.flush()


def run(stream, out):
    world = World(out)
    for raw in stream:
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, _, rest = line.strip().partition(" ")
        handler = COMMANDS.get(name)
        try:
            if handler is None:
                raise CommandError("unknown command %s" % name)
            handler(world, rest)
            invariant.check(world)
        except CommandError as exc:
            out.emit("error: %s" % exc)
        except InvariantViolation as exc:
            out.flush()
            sys.stderr.write("INVARIANT: %s\n" % exc)
            return EXIT_INVARIANT
    out.flush()
    return EXIT_OK


def main():
    stream = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", errors="replace")
    return run(stream, Output(sys.stdout))


if __name__ == "__main__":
    sys.exit(main())
