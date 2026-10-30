# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Evaluation budgets.

A Budget is created once per check (or per `eval` command) and handed down
through every evaluation that belongs to it.  Each evaluated AST node costs
one step; builtins that walk a list cost one further step per element.
"""
import limits
from errors import BudgetError


class Budget:
    def __init__(self, steps):
        self.limit = steps
        self.used = 0
        self.macro_depth = 0

    def charge(self, n=1):
        self.used += n
        if self.used >= self.limit:
            raise BudgetError("step limit %d exceeded" % self.limit)

    def enter_macro(self, name):
        self.macro_depth += 1
        if self.macro_depth > limits.MACRO_NEST:
            raise BudgetError("conditions nested deeper than %d at @%s" % (limits.MACRO_NEST, name))

    def leave_macro(self):
        self.macro_depth -= 1

    def remaining(self):
        return max(0, self.limit - self.used)
