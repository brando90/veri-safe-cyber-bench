# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""sitesmith: a small multi-tenant static site builder driven by a command script.

usage: python3 sitesmith.py WORKSPACE < commands.txt

Reads one command per line from stdin (see README.md) and exits with the
highest line status: 0 all fine, 2 some ERROR line, 4 some DENIED line.
"""

import os
import sys

from commands import Session


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: python3 sitesmith.py WORKSPACE < commands.txt\n")
        return 64
    workspace = argv[1]
    if not os.path.isdir(workspace):
        sys.stderr.write("sitesmith: no such workspace\n")
        return 64
    data = sys.stdin.buffer.read().decode("utf-8", "replace")
    session = Session(os.path.realpath(workspace))
    worst = 0
    for line in data.splitlines():
        worst = max(worst, session.execute(line))
    sys.stdout.flush()
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
