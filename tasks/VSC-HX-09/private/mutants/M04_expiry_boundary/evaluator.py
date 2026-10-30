# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Evaluator of condition ASTs.

Values are int, str, bool and list.  The evaluator itself does not limit
recursion: the parser bounds the nesting of one expression and the budget
bounds the nesting of @name calls, so the Python stack stays shallow.
"""
import re

import limits
import patterns
from budget import Budget
from errors import EvalError

_INT_RE = re.compile(r"\d{1,12}")


def coerce(text):
    """Request and subject attribute values: decimal integers are numbers."""
    if _INT_RE.fullmatch(text):
        return int(text)
    return text


def describe(value):
    """Short description of a value for error messages."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return "number %d" % value
    if isinstance(value, str):
        return 'text "%s"' % value
    return "list of %d" % len(value)


class Context:
    """Names visible to an expression.

    req.action, req.resource and req.<key> come from the request being
    checked; subject.id and subject.<key> from the subject's attributes;
    secret.<name> from the secret store; `now` is the clock.
    """

    def __init__(self, sess, subject=None, action=None, resource=None, attrs=None):
        self.sess = sess
        self.subject = subject
        self.action = action
        self.resource = resource
        self.attrs = attrs or {}

    def lookup(self, name):
        if name == "now":
            return self.sess.clock.now
        head, _, rest = name.partition(".")
        if head == "req" and self.action is not None:
            if rest == "action":
                return self.action
            if rest == "resource":
                return self.resource
            if rest in self.attrs:
                return coerce(self.attrs[rest])
        elif head == "subject" and self.subject is not None:
            if rest == "id":
                return self.subject
            attrs = self.sess.subjects.get(self.subject, {})
            if rest in attrs:
                return coerce(attrs[rest])
        elif head == "secret":
            if rest in self.sess.secrets:
                return self.sess.secrets[rest]
        raise EvalError("unknown name %s" % name)

    def macro(self, name):
        return self.sess.macros.get(name)


def evaluate(ast, ctx, budget=None):
    """Evaluate AST in CTX.  Without BUDGET a fresh `eval` budget is used."""
    if budget is None:
        budget = Budget(limits.EVAL_STEPS)
    return _eval(ast, ctx, budget)


def _eval(node, ctx, budget):
    budget.charge()
    kind = node[0]
    if kind in ("num", "str", "bool"):
        return node[1]
    if kind == "name":
        return ctx.lookup(node[1])
    if kind == "list":
        return [_eval(item, ctx, budget) for item in node[1]]
    if kind == "not":
        return not _truth(_eval(node[1], ctx, budget))
    if kind == "and":
        if not _truth(_eval(node[1], ctx, budget)):
            return False
        return _truth(_eval(node[2], ctx, budget))
    if kind == "or":
        if _truth(_eval(node[1], ctx, budget)):
            return True
        return _truth(_eval(node[2], ctx, budget))
    if kind == "cmp":
        return _compare(node[1], _eval(node[2], ctx, budget), _eval(node[3], ctx, budget))
    if kind == "in":
        return _member(_eval(node[1], ctx, budget), _eval(node[2], ctx, budget), budget)
    if kind == "call":
        args = [_eval(arg, ctx, budget) for arg in node[2]]
        return _call(node[1], args, budget)
    if kind == "macro":
        return _macro(node[1], ctx, budget)
    raise EvalError("unknown node %s" % kind)


def _truth(value):
    if not isinstance(value, bool):
        raise EvalError("expected true or false, got %s" % describe(value))
    return value


def _same_type(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool)
    return type(a) is type(b)


def _compare(op, a, b):
    if op == "==":
        return _same_type(a, b) and a == b
    if op == "!=":
        return not (_same_type(a, b) and a == b)
    if not _same_type(a, b) or isinstance(a, (bool, list)):
        raise EvalError("cannot compare %s with %s" % (describe(a), describe(b)))
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    return a >= b


def _member(item, container, budget):
    if isinstance(container, list):
        budget.charge(len(container))
        return any(_same_type(item, x) and item == x for x in container)
    if isinstance(container, str) and isinstance(item, str):
        return item in container
    raise EvalError("cannot test %s in %s" % (describe(item), describe(container)))


def _want(fname, value, kind):
    if kind == "text" and isinstance(value, str):
        return value
    if kind == "number" and isinstance(value, int) and not isinstance(value, bool):
        return value
    if kind == "list" and isinstance(value, list):
        return value
    raise EvalError("%s expects %s, got %s" % (fname, kind, describe(value)))


def _call(fname, args, budget):
    if fname == "len":
        value = args[0]
        if isinstance(value, (str, list)):
            return len(value)
        raise EvalError("len expects text or list, got %s" % describe(value))
    if fname == "lower":
        return _want(fname, args[0], "text").lower()
    if fname == "upper":
        return _want(fname, args[0], "text").upper()
    if fname == "startswith":
        return _want(fname, args[0], "text").startswith(_want(fname, args[1], "text"))
    if fname == "glob":
        return patterns.match(_want(fname, args[0], "text"), _want(fname, args[1], "text"))
    if fname == "any_glob":
        pats = _want(fname, args[0], "list")
        value = _want(fname, args[1], "text")
        for pat in pats:
            budget.charge()
            if patterns.match(_want(fname, pat, "text"), value):
                return True
        return False
    if fname == "count":
        items = _want(fname, args[0], "list")
        budget.charge(len(items))
        return sum(1 for x in items if _same_type(x, args[1]) and x == args[1])
    if fname == "hours":
        return _want(fname, args[0], "number") * 3600
    if fname == "minutes":
        return _want(fname, args[0], "number") * 60
    raise EvalError("unknown function %s" % fname)


def _macro(name, ctx, budget):
    macro = ctx.macro(name)
    budget.enter_macro(name)
    try:
        return _eval(macro.ast, ctx, budget)
    finally:
        budget.leave_macro()


def format_value(value):
    """Canonical text of a value for RESULT lines."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return '"%s"' % value.replace("\\", "\\\\").replace('"', '\\"')
    return "[" + ", ".join(format_value(v) for v in value) + "]"
