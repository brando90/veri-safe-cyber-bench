# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""relaydesk: read command lines on stdin, write results on stdout.

Run:  python3 main.py < commands.in
Exit status: 0 at the normal end of input, 86 if a documented invariant
does not hold (message "INVARIANT: ..." on stderr; output so far is kept).
"""

import sys

import commands
import dispatch
import lexer
import service
from errors import EXIT_INVARIANT, InvariantError


def read_lines(data):
    text = data.decode("utf-8", "replace")
    raw = text.split("\n")
    if raw and raw[-1] == "":
        raw.pop()
    for n, item in enumerate(raw, 1):
        if item.endswith("\r"):
            item = item[:-1]
        yield lexer.Line(item, n)


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    out = []
    svc = service.Service(out.append)
    dispatch.Dispatcher(svc)
    lines = read_lines(sys.stdin.buffer.read())
    ctx = commands.Context(lines)
    status = 0
    try:
        for line in lines:
            commands.run_line(svc, line, ctx)
            if len(out) > 256:
                sys.stdout.write("\n".join(out) + "\n")
                out.clear()
    except InvariantError as exc:
        status = EXIT_INVARIANT
        if out:
            sys.stdout.write("\n".join(out) + "\n")
            out.clear()
        sys.stdout.flush()
        sys.stderr.write("INVARIANT: %s\n" % exc)
        return status
    if out:
        sys.stdout.write("\n".join(out) + "\n")
    sys.stdout.flush()
    return status


if __name__ == "__main__":
    sys.exit(main())
