# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The redaction policy: named rules, prefix rules, keep list and strict mode."""
import copy

import names
from errors import CommandError

ACTIONS = ("drop", "redact", "pseudo", "mask")
KEEP = "keep"
RULE_WORDS = ACTIONS + (KEEP,)


class Policy:
    def __init__(self):
        self.named = {action: set() for action in ACTIONS}
        self.keep = set()
        self.prefixes = []
        self.strict = False
        self.salt = ""
        self._checks = None

    def add_rule(self, action, name):
        if action not in RULE_WORDS:
            raise CommandError("unknown action %s" % action)
        base = names.base(name)
        if not base:
            raise CommandError("empty name")
        if action == KEEP:
            self.keep.add(base)
        else:
            self.named[action].add(base)

    def add_prefix(self, prefix, action="redact"):
        if action not in ACTIONS:
            raise CommandError("unknown action %s" % action)
        base = names.base(prefix)
        if not base:
            raise CommandError("empty name")
        self.prefixes.append((base, action))
        self._checks = None

    def remove(self, name):
        base = names.base(name)
        found = False
        for table in list(self.named.values()) + [self.keep]:
            if base in table:
                table.discard(base)
                found = True
        before = len(self.prefixes)
        self.prefixes = [(p, a) for p, a in self.prefixes if p != base]
        if len(self.prefixes) != before:
            self._checks = None
            found = True
        return found

    def prefix_checks(self):
        if self._checks is None:
            checks = []
            for prefix, action in self.prefixes:
                checks.append((action, lambda base, p=prefix: base.startswith(p)))
            self._checks = checks
        return self._checks

    def action_for(self, name):
        """The action applied to a field called NAME, or None to pass it through.

        Explicit rules beat the keep list and strict mode; among explicit rules
        the strongest action (the order of ACTIONS) wins.
        """
        base = names.base(name)
        hits = set()
        for action in ACTIONS:
            if base in self.named[action]:
                hits.add(action)
        for action, check in self.prefix_checks():
            if check(base):
                hits.add(action)
        for action in ACTIONS:
            if action in hits:
                return action
        if self.strict and base not in self.keep:
            return "redact"
        return None

    def temporary(self, extra_keep):
        """A policy for one export."""
        temp = copy.deepcopy(self)
        temp.keep |= {names.base(n) for n in extra_keep}
        return temp

    def rule_count(self):
        return sum(len(t) for t in self.named.values()) + len(self.keep) + len(self.prefixes)
