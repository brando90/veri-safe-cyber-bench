# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""dun: add the late fee to every overdue invoice that has none yet."""
import currencies
import invoice
import ledger
import money
import timeutil
from invoice import Line

LATE_BP = 150


def late_fee(cur, outstanding):
    return max(cur.LATE_MIN, money.pct(outstanding, LATE_BP))


def cmd_dun(w, cmd):
    count = 0
    for inv in list(invoice.live(w)):
        if inv.late_day is not None or inv.outstanding() <= 0:
            continue
        if not timeutil.is_overdue(w.day, inv.due):
            continue
        cur = currencies.get(inv.currency)
        fee = late_fee(cur, inv.outstanding())
        inv.lines.append(Line("late", "late fee day=%d" % w.day, fee, "late"))
        inv.late += fee
        inv.total += fee
        inv.late_day = w.day
        ledger.post(w, "late", inv.cust, inv.number, fee)
        w.out.emit("late %s fee=%s" % (inv.number, currencies.money_text(cur, fee)))
        count += 1
    w.audit_add("dun", "day %d" % w.day, count)
    w.out.emit("dun applied=%d" % count)
