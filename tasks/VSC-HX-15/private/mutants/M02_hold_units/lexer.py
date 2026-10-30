# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Splits one command line into words and options."""
import re

from errors import CmdError

OPTION_RE = re.compile(r"^([a-z_]+)=(.*)$", re.S)
ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Word:
    __slots__ = ("text", "quoted")

    def __init__(self, text, quoted):
        self.text = text
        self.quoted = quoted


def tokenize(line):
    words = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            i += 1
        elif c == '"':
            i += 1
            buf = []
            while True:
                if i >= n:
                    raise CmdError("unterminated quote")
                c = line[i]
                if c == '"':
                    i += 1
                    break
                if c == "\\":
                    i += 1
                    if i >= n or line[i] not in ESCAPES:
                        raise CmdError("bad escape")
                    buf.append(ESCAPES[line[i]])
                else:
                    buf.append(c)
                i += 1
            words.append(Word("".join(buf), True))
        else:
            j = i
            while j < n and line[j] not in " \t":
                j += 1
            words.append(Word(line[i:j], False))
            i = j
    return words


def split_args(words):
    """Returns (positional texts, option dict)."""
    pos, opts = [], {}
    for w in words:
        m = None if w.quoted else OPTION_RE.match(w.text)
        if m:
            if m.group(1) in opts:
                raise CmdError("duplicate option %s" % m.group(1))
            opts[m.group(1)] = m.group(2)
        else:
            pos.append(w.text)
    return pos, opts
