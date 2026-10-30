# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Buffered standard output."""
import sys


class Output:
    def __init__(self, stream=None):
        self.stream = stream if stream is not None else sys.stdout
        self.buf = []

    def emit(self, line):
        self.buf.append(line)
        if len(self.buf) >= 512:
            self.flush()

    def flush(self):
        if self.buf:
            self.stream.write("\n".join(self.buf) + "\n")
            self.buf = []
        self.stream.flush()
