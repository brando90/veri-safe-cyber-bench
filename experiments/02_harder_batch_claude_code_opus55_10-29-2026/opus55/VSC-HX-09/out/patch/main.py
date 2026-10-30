#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""policyforge: read commands from standard input, print results.

    python3 main.py < commands.in

Each command's output is collected, the consistency check is run, and only
then is the output written.  A documented error prints `ERROR <category>:
<message>` (redacted) instead of the command's output.  A consistency
failure prints `INVARIANT: <text>` on standard error and exits with 86.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import commands  # noqa: E402
import invariant  # noqa: E402
import limits  # noqa: E402
import redact  # noqa: E402
from errors import InvariantViolation, PFError  # noqa: E402
from session import Session  # noqa: E402


class LineSource:
    """Iterator over input lines that command handlers can also read from."""

    def __init__(self, text):
        self.lines = text.split("\n")
        if self.lines and self.lines[-1] == "":
            self.lines.pop()
        self.pos = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.pos >= len(self.lines):
            raise StopIteration
        line = self.lines[self.pos]
        self.pos += 1
        return line[:-1] if line.endswith("\r") else line


def run(text, out):
    sess = Session()
    source = LineSource(text)
    for line in source:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            commands.execute(sess, stripped, source)
        except PFError as exc:
            sess.discard_output()
            sess.emit("ERROR %s: %s" % (exc.category, redact.scrub(sess, exc.message)))
        # Secret values never reach the output, whatever path produced a line.
        lines = [redact.scrub(sess, item) for item in sess.take_output()]
        try:
            invariant.check(sess, lines)
        except InvariantViolation as exc:
            out.flush()
            sys.stderr.write("INVARIANT: %s\n" % exc)
            return limits.INVARIANT_EXIT
        for item in lines:
            out.write(item + "\n")
    out.flush()
    return 0


def main():
    data = sys.stdin.buffer.read().decode("utf-8", "replace")
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    return run(data, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
