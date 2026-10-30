# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Splitting one input line into words and options.

Tokens are separated by spaces or tabs.  A token ``name=value`` whose name
is a lower-case identifier is an option; every other token is a word.
"""
import re

from errors import CommandError

OPT_RE = re.compile(r"([a-z][a-z0-9_]*)=(\S*)")


class Cmd:
    """One parsed command line."""

    __slots__ = ("words", "opts", "line")

    def __init__(self, words, opts, line):
        self.words = words
        self.opts = opts
        self.line = line

    @property
    def name(self):
        return self.words[0]

    def arity(self, low, high, usage):
        """Require between LOW and HIGH words after the command name."""
        n = len(self.words) - 1
        if n < low or n > high:
            raise CommandError("usage: %s" % usage)

    def allow(self, *names):
        for name in self.opts:
            if name not in names:
                raise CommandError("unknown option %s" % name)

    def opt(self, name, default=None):
        return self.opts.get(name, default)

    def word(self, i, default=None):
        if i < len(self.words):
            return self.words[i]
        return default


def parse(line):
    """Return a Cmd, or None for a blank line or a comment."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    words = []
    opts = {}
    for tok in text.split():
        m = OPT_RE.fullmatch(tok)
        if m is None:
            words.append(tok)
            continue
        name, value = m.group(1), m.group(2)
        if name in opts:
            raise CommandError("option %s given twice" % name)
        opts[name] = value
    if not words:
        raise CommandError("missing command")
    return Cmd(words, opts, text)
