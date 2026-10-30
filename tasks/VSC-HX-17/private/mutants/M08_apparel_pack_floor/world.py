# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The world: every table of the simulation and the command dispatcher."""
import cmdtable


class World:
    def __init__(self, out):
        self.out = out
        self.day = 0
        self.customers = {}
        self.orders = {}
        self.order_refs = {}
        self.lots = {}
        self.lot_seq = 0
        self.by_slot = {}
        self.moves = []
        self.shipments = []
        self.audit = []

    def audit_add(self, action, subject, *details):
        self.audit.append((len(self.audit) + 1, self.day, action, subject, tuple(str(d) for d in details)))

    def dispatch(self, cmd):
        handler = cmdtable.resolve(cmd)
        handler(self, cmd)
