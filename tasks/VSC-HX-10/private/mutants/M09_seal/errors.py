# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exception types and exit codes shared by the ledgerkeep modules.

* ``CommandError``: the command line is wrong or impossible.  The dispatcher
  prints ``error: MESSAGE``; nothing has changed.
* ``Deny``: a well-formed money operation was refused by a rule.  The
  dispatcher prints ``deny CODE [DETAIL]``; nothing has changed.
* ``InvariantViolation``: the consistency check found a state that the
  rules forbid.  ``INVARIANT: MESSAGE`` goes to standard error, exit 86.
"""

EXIT_OK = 0
EXIT_INVARIANT = 86


class LedgerError(Exception):
    """Base class of every ledgerkeep error."""


class CommandError(LedgerError):
    """Malformed or impossible command."""


class Deny(LedgerError):
    """A money operation refused by a rule."""

    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail

    def line(self):
        if self.detail:
            return "deny %s %s" % (self.code, self.detail)
        return "deny %s" % self.code


class InvariantViolation(LedgerError):
    """Internal consistency check failed (exit status 86)."""
