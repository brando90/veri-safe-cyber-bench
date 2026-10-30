# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""stockyard: a toy warehouse inventory and order-routing system.

Reads commands from standard input, one per line, and prints results on
standard output.  See README.md for the command set.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import invariant  # noqa: E402
import lexer  # noqa: E402
from errors import EXIT_INVARIANT, EXIT_OK, CommandError, InvariantViolation  # noqa: E402
from output import Output  # noqa: E402
from world import World  # noqa: E402


def run(stream, out):
    world = World(out)
    for raw in stream:
        line = raw.rstrip("\r\n")
        try:
            cmd = lexer.parse(line)
            if cmd is None:
                continue
            world.dispatch(cmd)
            invariant.full_check(world)
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
    out = Output()
    sys.exit(run(stream, out))


if __name__ == "__main__":
    main()
