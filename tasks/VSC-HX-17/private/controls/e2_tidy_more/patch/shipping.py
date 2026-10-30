# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""ship: turn the reserved stock of an order into shipments."""
import carriers
import customers
import money
import orders
import regions
import skus
import stock
import tiers
import warehouses
from errors import CommandError
from model import Shipment

PICKUP = "pickup"


def group_by_warehouse(order):
    groups = {}
    for line in order.lines:
        for alloc in line.allocs:
            groups.setdefault(alloc[0], []).append((line, alloc))
    return groups


def plan_group(w, order, cust, region, wh, items, hour, forced):
    """Everything about one shipment, worked out before anything changes."""
    qty = {}
    for line, alloc in items:
        lot = w.lots[alloc[1]]
        if stock.category_of(line.sku).is_expired(lot.expiry, w.day):
            raise CommandError("lot_expired", lot.id)
        qty[line.sku] = qty.get(line.sku, 0) + alloc[2]
    weight = sum(stock.category_of(s).weight(q) for s, q in qty.items())
    haz = max(stock.category_of(s).HAZ for s in qty)
    goods = sum(skus.price(s) * q for s, q in qty.items())
    distance = wh.distance(region.CODE, region.ZONE)
    if region.ZONE < 0:
        carrier, cost, transit = PICKUP, 0, 0
    else:
        car = carriers.choose(forced or cust.carrier, region, wh, weight, haz, distance)
        carrier, cost, transit = car.CODE, car.cost(weight, distance), car.transit(distance)
    freight = 0
    if not tiers.free_freight(cust.tier, order.goods):
        freight = cost + region.REMOTE_FEE if carrier != PICKUP else 0
    handling = 0 if tiers.free_freight(cust.tier, order.goods) else wh.handling(len(qty), sum(qty.values()))
    dutiable = region.dutiable(goods)
    ship_day = wh.ship_day(w.day, hour)
    eta = region.delivery_day(ship_day + transit, dutiable)
    return {"qty": qty, "weight": weight, "goods": goods, "carrier": carrier,
            "freight": freight, "handling": handling, "duty": region.duty(goods),
            "ship_day": ship_day, "eta": eta, "items": items}


def cmd_ship(w, cmd):
    cmd.allow("at", "carrier")
    order = orders.find(w, cmd.arg(0))
    cust = customers.open(w, order.cust)
    hour = money.parse_int(cmd.opt("at", "10"), 0, 23)
    forced = cmd.opt("carrier")
    if forced is not None:
        carriers.checked(forced)
    groups = group_by_warehouse(order)
    if not groups:
        raise CommandError("nothing_pending", order.number)
    region = regions.get(cust.region)
    plans = [(code, plan_group(w, order, cust, region, warehouses.get(code), groups[code],
                               hour, forced)) for code in sorted(groups)]
    for code, plan in plans:
        ship_id = "SHP-%04d" % (len(w.shipments) + 1)
        for line, alloc in plan["items"]:
            stock.consume(w, [alloc], ship_id)
            line.allocs.remove(alloc)
            line.shipped += alloc[2]
            line.ship_day = w.day
            line.ship_wh = code
        w.shipments.append(Shipment(
            ship_id, order.number, code, plan["carrier"], sorted(plan["qty"].items()),
            plan["weight"], plan["goods"], plan["freight"], plan["handling"], plan["duty"],
            w.day, plan["ship_day"], plan["eta"], region.CODE))
        w.out.emit("shipment %s order %s from %s carrier %s weight %s goods %s freight %s "
                   "handling %s duty %s dispatch day %d eta day %d" % (
                       ship_id, order.number, code, plan["carrier"], money.grams(plan["weight"]),
                       money.fmt(plan["goods"]), money.fmt(plan["freight"]),
                       money.fmt(plan["handling"]), money.fmt(plan["duty"]),
                       plan["ship_day"], plan["eta"]))
    orders.refresh(order)
    w.audit_add("ship", order.cust, order.number, len(plans))
