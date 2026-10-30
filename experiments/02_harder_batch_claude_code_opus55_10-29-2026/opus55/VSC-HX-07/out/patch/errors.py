# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exception types and exit codes shared by every quotagate module.

Three kinds of trouble exist and each has exactly one way of being reported:

* ``CommandError``: the command line itself is wrong (unknown command, bad
  value, unknown tenant ...).  The dispatcher prints ``error: MESSAGE`` and
  carries on with the next line.  Nothing has changed.
* ``Deny``: a well-formed request or job was refused by the admission
  pipeline.  The caller prints ``deny CODE [DETAIL]`` (or the job form of it)
  and writes an audit record.  Nothing else has changed.
* ``InvariantViolation``: the program's own consistency check found a state
  that the rules in README.md forbid.  The dispatcher prints
  ``INVARIANT: MESSAGE`` on standard error and exits with status 86.
"""

EXIT_OK = 0
EXIT_INVARIANT = 86


class GateError(Exception):
    """Base class for every quotagate error."""


class CommandError(GateError):
    """Malformed or impossible command; printed as ``error: MESSAGE``."""


class Deny(GateError):
    """A request refused by admission control.

    ``code`` is one of the documented refusal codes (auth, nonce-required,
    stale, replay, rate, quota-requests, quota-egress); ``detail`` is an
    optional ``key=value`` tail that is printed after the code.
    """

    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail

    def line(self):
        if self.detail:
            return "deny %s %s" % (self.code, self.detail)
        return "deny %s" % self.code

    def short(self):
        """The code with the first word of the detail (used in audit results)."""
        return self.code


class InvariantViolation(GateError):
    """Internal consistency check failed (exit status 86)."""
