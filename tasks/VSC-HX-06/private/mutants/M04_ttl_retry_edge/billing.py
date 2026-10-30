# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Billing (README, "Billing").

Every delivered message is billed to its sender as one line:

    amount = (plan base + plan rate per KiB * size / 1024) * priority factor

in cents, kept exact (Fraction) until it is shown or added up; money.py
rounds each line to whole cents and adds rounded lines.  Failed, expired
and cancelled messages are not billed.
"""

from fractions import Fraction

import money
import units


class Plan:
    __slots__ = ("name", "base", "per_kib")

    def __init__(self, name, base, per_kib):
        self.name = name
        self.base = base          # cents per message
        self.per_kib = per_kib    # cents per KiB of body, pro rata


PLANS = {
    "basic": Plan("basic", Fraction(3, 2), Fraction(4, 5)),
    "bulk": Plan("bulk", Fraction(3, 5), Fraction(2, 5)),
    "pro": Plan("pro", Fraction(5, 2), Fraction(0)),
}

PRIORITY_FACTOR = {
    "urgent": Fraction(3, 2),
    "high": Fraction(6, 5),
    "normal": Fraction(1),
    "low": Fraction(1),
}


class Line:
    __slots__ = ("msg_id", "sender", "recipient", "plan", "at", "size", "prio",
                 "amount", "invoice")

    def __init__(self, msg_id, sender, recipient, plan, at, size, prio, amount):
        self.msg_id = msg_id
        self.sender = sender
        self.recipient = recipient
        self.plan = plan
        self.at = at
        self.size = size
        self.prio = prio
        self.amount = amount
        self.invoice = None

    def cents(self):
        return money.cents(self.amount)


def line_amount(plan, size, prio):
    volume = plan.per_kib * Fraction(size, units.BYTES_PER_KIB)
    return (plan.base + volume) * PRIORITY_FACTOR[prio]


class Billing:
    def __init__(self):
        self.lines = []
        self._next_invoice = {}

    def charge(self, msg, plan_name, at):
        plan = PLANS[plan_name]
        line = Line(msg.id, msg.sender, msg.recipient, plan_name, at, msg.size,
                    msg.prio, line_amount(plan, msg.size, msg.prio))
        self.lines.append(line)
        return line

    def open_lines(self, sender):
        return [l for l in self.lines if l.sender == sender and l.invoice is None]

    def close(self, sender):
        """Assign the next invoice number of SENDER to its open lines."""
        lines = self.open_lines(sender)
        if not lines:
            return None, []
        number = self._next_invoice.get(sender, 1)
        self._next_invoice[sender] = number + 1
        for line in lines:
            line.invoice = number
        return number, lines

    def amounts(self, plan=None, sender=None):
        return [l.amount for l in self.lines
                if (plan is None or l.plan == plan) and (sender is None or l.sender == sender)]

    def count(self, plan=None):
        return sum(1 for l in self.lines if plan is None or l.plan == plan)
