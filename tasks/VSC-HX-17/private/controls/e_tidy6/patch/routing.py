# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Choosing the warehouses that fill an order and reserving the stock."""
import regions
import stock
import warehouses


def candidates(region):
    """Warehouse modules for a destination, nearest first, ties by code."""
    return sorted(warehouses.all_modules(),
                  key=lambda wh: (wh.distance(region.CODE, region.ZONE), wh.CODE))


def take(w, wh, line, qty):
    allocs = stock.reserve(w, wh.CODE, line.sku, qty)
    got = sum(a[2] for a in allocs)
    line.allocs = stock.merge_allocs(line.allocs + allocs)
    line.backorder -= got
    return got


def allocate(w, order, cust):
    """Reserve stock for every backordered line of ORDER.  One warehouse
    takes the whole lot if any can; otherwise, when the customer accepts split
    shipments, each line is filled from the nearest warehouses in turn."""
    todo = [line for line in order.lines if line.backorder > 0]
    if not todo:
        return 0
    region = regions.get(cust.region)
    cands = candidates(region)
    for wh in cands:
        if all(stock.available(w, wh.CODE, line.sku) >= line.backorder for line in todo):
            return sum(take(w, wh, line, line.backorder) for line in todo)
    if not cust.split:
        return 0
    total = 0
    for line in todo:
        for wh in cands:
            if line.backorder == 0:
                break
            have = stock.available(w, wh.CODE, line.sku)
            if have > 0:
                total += take(w, wh, line, min(have, line.backorder))
    return total
