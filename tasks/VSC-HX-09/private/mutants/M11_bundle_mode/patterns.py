# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Resource and action names and the patterns that select them.

Resources are paths: "/" followed by one or more non-empty segments made of
letters, digits and . _ ~ -.  A resource pattern has the same shape, but a
segment may be `*` (exactly one segment) and the last segment may be `**`
(zero or more segments).  `/a/**` therefore selects `/a` itself and every
resource below it.

Actions are `namespace:verb`.  An action pattern is `*` (every action), or
`ns:*`, `*:verb`, or an exact action.

This module is the only implementation of the matching rule; every part of
the program that selects resources or actions by pattern calls match().
"""
import re

from errors import RuleError

_SEG_RE = re.compile(r"[A-Za-z0-9._~-]+")
_WORD_RE = re.compile(r"[a-z][a-z0-9_-]*")


def is_resource_pattern(text):
    return text.startswith("/")


def check_resource(text, pattern=True):
    """Validate a resource (pattern=False) or a resource pattern."""
    what = "resource pattern" if pattern else "resource"
    if not text.startswith("/") or len(text) > 200:
        raise RuleError("bad %s %s" % (what, text))
    segs = text[1:].split("/")
    for i, seg in enumerate(segs):
        if pattern and seg == "*":
            continue
        if pattern and seg == "**":
            if i != len(segs) - 1:
                raise RuleError("** must be the last segment in %s" % text)
            continue
        if not _SEG_RE.fullmatch(seg):
            raise RuleError("bad %s %s" % (what, text))
    return text


def check_action(text, pattern=True):
    """Validate an action (pattern=False) or an action pattern."""
    what = "action pattern" if pattern else "action"
    if pattern and text == "*":
        return text
    ns, sep, verb = text.partition(":")
    if not sep:
        raise RuleError("bad %s %s" % (what, text))
    for part in (ns, verb):
        if pattern and part == "*":
            continue
        if not _WORD_RE.fullmatch(part):
            raise RuleError("bad %s %s" % (what, text))
    return text


def match_resource(pattern, value):
    if pattern.endswith("/**") and "*" not in pattern[:-3]:
        # Fast path for the most common shape: a literal prefix plus /**.
        base = pattern[:-3]
        return value == base or value.startswith(base + "/")
    return _match_segments(pattern[1:].split("/"), value[1:].split("/"))


def _match_segments(pat, val):
    if pat and pat[-1] == "**":
        head = pat[:-1]
        if len(val) < len(head):
            return False
        return all(p == "*" or p == v for p, v in zip(head, val))
    if len(pat) != len(val):
        return False
    return all(p == "*" or p == v for p, v in zip(pat, val))


def match_action(pattern, action):
    if pattern == "*":
        return True
    pns, _, pverb = pattern.partition(":")
    ans, _, averb = action.partition(":")
    return pns in ("*", ans) and pverb in ("*", averb)


def match(pattern, value):
    """Match a resource pattern (leading /) or an action pattern."""
    if is_resource_pattern(pattern):
        return value.startswith("/") and match_resource(pattern, value)
    return match_action(pattern, value)


def specificity(pattern):
    """Sort key: larger is more specific.  Literal segments count most,
    then single-segment wildcards; a trailing ** counts least."""
    if pattern == "*":
        return (0, 0, 0)
    if is_resource_pattern(pattern):
        segs = pattern[1:].split("/")
        literal = sum(1 for s in segs if s not in ("*", "**"))
        single = sum(1 for s in segs if s == "*")
        return (literal, single, 0 if segs[-1] == "**" else 1)
    ns, _, verb = pattern.partition(":")
    return (int(ns != "*") + int(verb != "*"), 0, 1)
