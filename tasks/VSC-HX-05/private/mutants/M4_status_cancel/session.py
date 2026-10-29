# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Session state: database connection, current actor, pending output."""

import roles
import store
from errors import Denied


class Session:
    def __init__(self, lines, out):
        roles.reset()
        self.conn = store.connect(roles.BUILTIN, roles.FIRST_USER)
        self.lines = lines          # iterator over input lines (shared with blocks)
        self.out = out
        self.actor = None           # None is the actor "nobody"
        self.expect = None          # invariant.Expect of the running command
        self.pending = []

    # -- actor and permissions ------------------------------------------------

    def actor_name(self):
        return self.actor if self.actor is not None else "nobody"

    def role(self):
        if self.actor is None:
            return None
        return store.user_role(self.conn, self.actor)

    def holds(self, perm):
        return roles.can(self.conn, self.role(), perm)

    def require(self, perm):
        """Raise Denied unless the actor holds PERM."""
        if not self.holds(perm):
            raise Denied(perm)

    # -- output ---------------------------------------------------------------

    def emit(self, text):
        """Queue one output line; it is printed only if the command succeeds."""
        self.pending.append(text)

    def discard(self):
        self.pending = []

    def flush(self):
        for text in self.pending:
            self.out.write(text + "\n")
        self.pending = []
