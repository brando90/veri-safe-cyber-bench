# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Error types used across policyforge.

Every user-visible failure is a PFError subclass.  main.py prints it as
`ERROR <category>: <message>` (after secret redaction) and continues with
the next command.  A command that fails leaves no output besides that line
and changes nothing, so handlers validate first and mutate last.
"""


class PFError(Exception):
    """Base class of the documented, recoverable errors."""

    category = "error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message


class UsageError(PFError):
    category = "usage"


class ParseError(PFError):
    category = "parse"


class EvalError(PFError):
    category = "eval"


class BudgetError(EvalError):
    """A step or nesting budget ran out while evaluating an expression."""

    category = "budget"


class RuleError(PFError):
    category = "rule"


class SetError(PFError):
    category = "set"


class ApprovalError(PFError):
    category = "approval"


class BundleError(PFError):
    category = "bundle"


class TemplateError(PFError):
    category = "template"


class LogError(PFError):
    category = "log"


class SecretError(PFError):
    category = "secret"


class ClockError(PFError):
    category = "clock"


class InvariantViolation(Exception):
    """Internal consistency failure.  main.py reports it on standard error
    as `INVARIANT: <text>` and stops with exit status 86."""
