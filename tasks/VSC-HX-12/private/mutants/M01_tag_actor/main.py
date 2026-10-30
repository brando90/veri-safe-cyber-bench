# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""crateyard: a toy package registry simulator.

Reads commands from standard input, one per line, and prints results on
standard output.  See README.md for the command set.
"""
import io
import sys

import invariant
import lexer
from errors import EXIT_INVARIANT, EXIT_OK, CommandError, InvariantViolation
from output import Output
from world import World


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
    return run(stream, Output(sys.stdout))


if __name__ == "__main__":
    sys.exit(main())
