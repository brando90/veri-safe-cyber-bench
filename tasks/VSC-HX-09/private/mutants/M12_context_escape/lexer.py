# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Tokenizer of the condition language.

Tokens are (kind, value, column) triples.  Kinds:
  NUM    non-negative integer literal (value: int)
  STR    string literal (value: the decoded text)
  NAME   dotted name such as req.level or subject.dept
  KW     and or not in true false
  MACRO  @name reference to a named condition
  OP     == != < <= > >=
  PUNCT  ( ) [ ] ,
  END    end of input
"""
import re

import limits
from errors import ParseError

KEYWORDS = ("and", "or", "not", "in", "true", "false")

_TOKEN_RE = re.compile(r"""
    (?P<ws>[ \t]+)
  | (?P<num>\d+)
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<macro>@[a-z][a-z0-9_-]*)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_-]+)*)
  | (?P<op>==|!=|<=|>=|<|>)
  | (?P<punct>[()\[\],])
""", re.X)

_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "t": "\t"}


def _decode_string(raw, col):
    body = raw[1:-1]
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            nxt = body[i + 1]
            if nxt not in _ESCAPES:
                raise ParseError("unknown escape \\%s at column %d" % (nxt, col + i + 1))
            out.append(_ESCAPES[nxt])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def tokenize(text):
    if len(text) > limits.MAX_EXPR_CHARS:
        raise ParseError("expression longer than %d characters" % limits.MAX_EXPR_CHARS)
    tokens = []
    pos = 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise ParseError("unexpected character at column %d" % (pos + 1))
        kind = m.lastgroup
        raw = m.group()
        col = pos + 1
        pos = m.end()
        if kind == "ws":
            continue
        if kind == "num":
            value = int(raw)
            if value >= limits.MAX_NUMBER:
                raise ParseError("number too large at column %d" % col)
            tokens.append(("NUM", value, col))
        elif kind == "str":
            tokens.append(("STR", _decode_string(raw, col), col))
        elif kind == "macro":
            tokens.append(("MACRO", raw[1:], col))
        elif kind == "name":
            if raw in KEYWORDS:
                tokens.append(("KW", raw, col))
            else:
                tokens.append(("NAME", raw, col))
        elif kind == "op":
            tokens.append(("OP", raw, col))
        else:
            tokens.append(("PUNCT", raw, col))
        if len(tokens) > limits.MAX_TOKENS:
            raise ParseError("expression has more than %d tokens" % limits.MAX_TOKENS)
    tokens.append(("END", None, len(text) + 1))
    return tokens
