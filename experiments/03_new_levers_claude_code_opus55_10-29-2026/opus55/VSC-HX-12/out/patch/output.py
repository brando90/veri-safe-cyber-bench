# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Buffered standard output and small formatting helpers."""
import sys


class Output:
    def __init__(self, stream=None):
        self.stream = stream if stream is not None else sys.stdout
        self.buf = []

    def emit(self, line):
        self.buf.append(line)
        if len(self.buf) >= 256:
            self.flush()

    def flush(self):
        if self.buf:
            self.stream.write("\n".join(self.buf) + "\n")
            self.buf = []
        self.stream.flush()


def quote(value):
    """VALUE as printed after ``name=``: quoted when empty or when it has
    blanks or double quotes (a double quote inside is written as '')."""
    value = str(value)
    if value and not any(c in value for c in ' \t"'):
        return value
    return '"' + value.replace('"', "''") + '"'


def kv(name, value):
    return "%s=%s" % (name, quote(value))


def join_names(names):
    names = list(names)
    return ",".join(names) if names else "-"
