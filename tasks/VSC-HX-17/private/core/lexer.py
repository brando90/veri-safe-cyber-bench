# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Splitting one input line into words and options.

A line is a sequence of tokens separated by spaces or tabs.  A double quote
starts a quoted part that runs to the next double quote; quoted parts may
contain spaces and are glued to the characters around them in the same
token.  A token name=value whose name is a lower-case identifier is an
option; every other token is a word.  A line that is blank or starts with #
is skipped.
"""
import re

from errors import CommandError

OPT_RE = re.compile(r"([a-z][a-z0-9_]*)=(.*)", re.S)


class Cmd:
    """One parsed command line."""

    def __init__(self, words, opts, line):
        self.words = words
        self.opts = opts
        self.line = line
        self.name = ""
        self.args = []
        self.usage = ""

    def arg(self, i, default=None):
        if i < len(self.args):
            return self.args[i]
        if default is not None:
            return default
        raise CommandError("usage", self.usage)

    def opt(self, name, default=None):
        return self.opts.get(name, default)

    def allow(self, *names):
        for key in self.opts:
            if key not in names:
                raise CommandError("bad_option", key)


def tokenize(line):
    toks = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] in " \t":
            i += 1
            continue
        quoted = line[i] == '"'
        buf = []
        while i < n and line[i] not in " \t":
            if line[i] == '"':
                j = line.find('"', i + 1)
                if j < 0:
                    raise CommandError("bad_quoting")
                buf.append(line[i + 1:j])
                i = j + 1
            else:
                buf.append(line[i])
                i += 1
        toks.append(("".join(buf), quoted))
    return toks


def parse(line):
    """Cmd for LINE, or None for a blank line or a comment."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    words = []
    opts = {}
    for tok, quoted in tokenize(text):
        m = None if quoted else OPT_RE.fullmatch(tok)
        if m is None:
            words.append(tok)
            continue
        key, value = m.group(1), m.group(2)
        if key in opts:
            raise CommandError("dup_option", key)
        opts[key] = value
    if not words:
        raise CommandError("unknown_command", text.split()[0])
    return Cmd(words, opts, text)
