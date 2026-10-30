# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Session state: everything one run of the program knows."""
from approvals import ApprovalBook
from clock import Clock
from decisionlog import DecisionLog
from macros import MacroTable
from policies import PolicyStore


class Session:
    def __init__(self):
        self.clock = Clock()
        self.store = PolicyStore()
        self.macros = MacroTable()
        self.secrets = {}           # name -> value
        self.subjects = {}          # subject -> {key: value}
        self.approvals = ApprovalBook()
        self.log = DecisionLog()
        self.templates = {}         # name -> template.Template
        self._out = []

    def emit(self, line):
        self._out.append(line)

    def emit_all(self, lines):
        self._out.extend(lines)

    def take_output(self):
        lines = self._out
        self._out = []
        return lines

    def discard_output(self):
        self._out = []
