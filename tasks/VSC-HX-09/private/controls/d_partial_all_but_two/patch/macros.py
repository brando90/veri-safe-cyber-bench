# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Named conditions (`cond define NAME EXPR`, used as @NAME).

A named condition can only refer to conditions defined before it and can
never be redefined or removed, so the reference graph has no cycles.
"""
import re

import limits
import parser
from errors import ParseError, UsageError

_NAME_RE = re.compile(limits.NAME_PATTERN)


class Macro:
    def __init__(self, name, text, ast, refs):
        self.name = name
        self.text = text
        self.ast = ast
        self.refs = refs


class MacroTable:
    def __init__(self):
        self.items = {}

    def define(self, name, text):
        if not _NAME_RE.fullmatch(name):
            raise UsageError("bad condition name %s" % name)
        if name in self.items:
            raise UsageError("condition %s is already defined" % name)
        ast = parser.parse_expr(text)
        refs = parser.macro_refs(ast)
        self.check_refs(refs)
        macro = Macro(name, text.strip(), ast, refs)
        self.items[name] = macro
        return macro

    def check_refs(self, refs):
        for ref in refs:
            if ref not in self.items:
                raise ParseError("unknown condition @%s" % ref)

    def get(self, name):
        return self.items[name]

    def names(self):
        return sorted(self.items)


def compile_condition(table, text):
    """Parse a rule or approval condition and check its @references."""
    ast = parser.parse_expr(text)
    table.check_refs(parser.macro_refs(ast))
    return ast
