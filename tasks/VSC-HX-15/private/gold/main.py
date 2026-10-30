# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""chillroute: a toy cold-chain shipment monitor.

Reads commands from standard input, one per line, and prints results on
standard output.  See README.md for the command set.
"""
import sys

import dispatch
from world import World


def main():
    data = sys.stdin.buffer.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        sys.stdout.write("error: input is not valid UTF-8\n")
        return 2
    world = World()
    dispatch.run(world, text)
    out = "".join(line + "\n" for line in world.lines)
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
