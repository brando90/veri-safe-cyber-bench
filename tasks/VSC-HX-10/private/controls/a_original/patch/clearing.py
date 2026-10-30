# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The simulated clearing house that settlement batches are submitted to.

Its answers are scripted: ``clearing fail N`` makes the next N submissions
fail; every other submission is accepted.
"""


class Clearing:
    def __init__(self):
        self.fail_next = 0
        self.submitted = 0
        self.accepted = 0

    def script_failures(self, n):
        self.fail_next = n

    def submit(self, batch):
        self.submitted += 1
        if self.fail_next > 0:
            self.fail_next -= 1
            return False
        self.accepted += 1
        return True
