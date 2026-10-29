# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""slotbook: read command lines on stdin, write results on stdout.

Run:  python3 main.py < commands.in
Exit status: 0 at the normal end of input, 86 if the internal consistency
check fails (message "INVARIANT: ..." on stderr; output so far is kept).
"""

import sys

import invariant
import registry
import session


def read_lines(data):
    text = data.decode("utf-8", "replace")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [l[:-1] if l.endswith("\r") else l for l in lines]


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    lines = iter(read_lines(sys.stdin.buffer.read()))
    sess = session.Session(lines, sys.stdout)
    try:
        for line in sess.lines:
            registry.run_line(sess, line)
    except invariant.InvariantError as exc:
        sys.stdout.flush()
        sys.stderr.write("INVARIANT: %s\n" % exc)
        return invariant.EXIT_CODE
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
