# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exception types shared by every slotbook module.

A CommandError means "this command cannot be carried out": the dispatcher
rolls the database back to the state before the command, discards any output
the command had prepared and prints "ERROR <message>".
"""


class CommandError(Exception):
    """The command is refused; str(exc) is printed after 'ERROR '."""


class Denied(CommandError):
    """The actor lacks a permission the command needs."""

    def __init__(self, perm):
        super().__init__("denied: " + perm)
        self.perm = perm


class DbError(CommandError):
    """A database statement failed.  Valid input never produces this."""

    def __init__(self, message):
        super().__init__("db: " + message)
