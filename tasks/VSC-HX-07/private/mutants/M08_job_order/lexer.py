# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Splitting one input line into words and options.

A line is a sequence of tokens separated by spaces or tabs.  A double quote
starts a quoted part that runs to the next double quote; quoted parts may
contain spaces and are glued to the surrounding characters of the same
token (``label="front desk"`` is one token).  There is no escape character:
a backslash is an ordinary character.  A token of the form ``name=value``
whose name is a lower-case dotted identifier is an option; every other token
is a word.  A token that begins with a double quote is always a word.
"""
import re

from errors import CommandError

OPT_RE = re.compile(r"([a-z][a-z0-9_]*(?:\.[a-z0-9_]+)*)=(.*)", re.S)


class Token:
    __slots__ = ("text", "lead_quote")

    def __init__(self, text, lead_quote):
        self.text = text
        self.lead_quote = lead_quote


class Cmd:
    """One parsed command line."""

    def __init__(self, words, opts, line):
        self.words = words
        self.opts = opts
        self.line = line

    @property
    def name(self):
        return self.words[0]

    def opt(self, name, default=None):
        return self.opts.get(name, default)

    def prefixed(self, prefix):
        """Options whose name starts with PREFIX, with the prefix removed."""
        return {k[len(prefix):]: v for k, v in self.opts.items() if k.startswith(prefix)}


def tokenize(line):
    toks = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] in " \t":
            i += 1
            continue
        lead_quote = line[i] == '"'
        buf = []
        while i < n and line[i] not in " \t":
            if line[i] == '"':
                j = line.find('"', i + 1)
                if j < 0:
                    raise CommandError("unterminated quote")
                buf.append(line[i + 1:j])
                i = j + 1
            else:
                buf.append(line[i])
                i += 1
        toks.append(Token("".join(buf), lead_quote))
    return toks


def parse(line):
    """Return a Cmd, or None for blank lines and comments."""
    stripped = line.strip(" \t")
    if not stripped or stripped.startswith("#"):
        return None
    words = []
    opts = {}
    for tok in tokenize(stripped):
        m = None if tok.lead_quote else OPT_RE.fullmatch(tok.text)
        if m is None:
            words.append(tok.text)
            continue
        name, value = m.group(1), m.group(2)
        if name in opts:
            raise CommandError("option %s given twice" % name)
        opts[name] = value
    if not words:
        raise CommandError("missing command")
    return Cmd(words, opts, stripped)


def need(cmd, lo, hi, usage):
    """Check the number of words (command name included)."""
    if not lo <= len(cmd.words) <= hi:
        raise CommandError("usage: %s" % usage)


def allow_opts(cmd, names, prefixes=()):
    for name in cmd.opts:
        if name in names:
            continue
        if any(name.startswith(p) and len(name) > len(p) for p in prefixes):
            continue
        raise CommandError("%s: unknown option %s" % (cmd.words[0], name))
