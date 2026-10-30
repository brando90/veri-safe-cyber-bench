# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version requirements.

A requirement is ``*`` or a comma-separated list of clauses, each one of
``=V``, ``>=V``, ``>V``, ``<=V``, ``<V``, ``^V``, ``~V`` or a bare ``V``
(the same as ``^V``).  ``parse`` returns None for text it cannot read.
"""
import semver

_OPS = ("<=", ">=", "=", "<", ">", "^", "~")


class Requirement:
    __slots__ = ("text", "bounds", "pre_cores", "kind")

    def __init__(self, text, bounds, pre_cores, kind):
        self.text = text
        self.bounds = bounds
        self.pre_cores = pre_cores
        self.kind = kind

    def __repr__(self):
        return "Requirement(%s)" % self.text


def _split_op(clause):
    for op in _OPS:
        if clause.startswith(op):
            return op, clause[len(op):]
    return "^", clause


def _caret_upper(v, given):
    if v.major > 0 or given == 1:
        return semver.Version(v.major + 1, 0, 0)
    if v.minor > 0 or given == 2:
        return semver.Version(0, v.minor + 1, 0)
    return semver.Version(0, 0, v.patch + 1)


def _tilde_upper(v, given):
    if given == 1:
        return semver.Version(v.major + 1, 0, 0)
    return semver.Version(v.major, v.minor + 1, 0)


def _clause_bounds(op, v, given):
    if op == "=":
        return [("=", v)]
    if op in (">=", ">", "<=", "<"):
        return [(op, v)]
    upper = _caret_upper(v, given) if op == "^" else _tilde_upper(v, given)
    return [(">=", v), ("<", upper)]


def parse(text):
    if text is None:
        return None
    text = text.strip()
    if text == "*":
        return Requirement("*", [], frozenset(), "range")
    if not text or len(text) > 64:
        return None
    bounds = []
    pre_cores = set()
    clauses = [c.strip() for c in text.split(",")]
    for clause in clauses:
        op, rest = _split_op(clause)
        v, given = semver.parse_partial(rest.strip())
        if v is None or (op == "=" and given != 3):
            return None
        if v.pre:
            pre_cores.add(v.core)
        bounds.extend(_clause_bounds(op, v, given))
    kind = "exact" if len(clauses) == 1 and bounds[0][0] == "=" else "range"
    return Requirement(text, bounds, frozenset(pre_cores), kind)


def matches(req, v):
    if v.pre and v.core not in req.pre_cores:
        return False
    k = semver.key(v)
    for op, b in req.bounds:
        bk = semver.key(b)
        if op == "=" and k != bk:
            return False
        if op == ">=" and k < bk:
            return False
        if op == ">" and k <= bk:
            return False
        if op == "<=" and k > bk:
            return False
        if op == "<" and k >= bk:
            return False
    return True
