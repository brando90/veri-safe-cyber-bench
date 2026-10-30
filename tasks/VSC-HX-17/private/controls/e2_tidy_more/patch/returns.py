# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""return: take shipped goods back, restocking them or scrapping them."""
import customers
import money
import orders
import stock
from errors import CommandError


def cmd_return(w, cmd):
    cmd.allow("cond")
    order = orders.find(w, cmd.arg(0))
    customers.open(w, order.cust)
    sku = cmd.arg(1)
    line = next((x for x in order.lines if x.sku == sku), None)
    if line is None:
        raise CommandError("unknown_sku", sku)
    qty = money.parse_int(cmd.arg(2), 1, 999999)
    cond = cmd.opt("cond", "good")
    if cond not in ("good", "damaged"):
        raise CommandError("bad_cond", cond)
    room = line.shipped - line.returned
    if qty > room:
        raise CommandError("return_excess", room, sku, order.number)
    cat = stock.category_of(sku)
    if not cat.return_ok(w.day - line.ship_day):
        raise CommandError("return_window", sku)
    line.returned += qty
    if cat.disposition(cond) == "restock":
        stock.new_lot(w, line.ship_wh, sku, qty, None)
        stock.record(w, "return", line.ship_wh, sku, qty, ref=order.number)
        what = "restocked"
    else:
        stock.record(w, "scrap", line.ship_wh, sku, 0, qty=qty, ref=order.number)
        what = "scrapped"
    w.audit_add("return", order.cust, order.number, sku, qty, what)
    w.out.emit("return %s %s x%d %s at %s" % (order.number, sku, qty, what, line.ship_wh))
