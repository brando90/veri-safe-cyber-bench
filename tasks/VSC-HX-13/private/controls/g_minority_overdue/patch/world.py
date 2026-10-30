# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The world: every table of the simulation and the command dispatcher."""
import cmdtable


class World:
    def __init__(self, out):
        self.out = out
        self.day = 0
        self.customers = {}
        self.invoices = {}
        self.by_cust = {}
        self.usage = []
        self.usage_by = {}
        self.usage_ids = set()
        self.ledger = []
        self.credit_sum = {}
        self.audit = []
        self.seq = 0

    def audit_add(self, action, subject, *details):
        self.audit.append((len(self.audit) + 1, self.day, action, subject, tuple(str(d) for d in details)))

    def dispatch(self, cmd):
        handler = cmdtable.resolve(cmd)
        handler(self, cmd)
