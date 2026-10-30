# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Invoice numbers: one sequence for the whole run, never reused."""


def next_number(w):
    w.seq += 1
    return "INV-%04d" % w.seq
