# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Lots of stock: where goods are, how much of it is free, and every change."""
import categories
import skus
from model import Lot, Move


def pick_key(lot):
    """Order in which lots are picked: earliest expiry first, then by id;
    lots without an expiry come last, oldest first."""
    if lot.expiry is None:
        return (1, 0, lot.id)
    return (0, lot.expiry, lot.id)


def category_of(sku):
    return categories.get(skus.category(sku))


def lots_of(w, wh, sku):
    return sorted((w.lots[i] for i in w.by_slot.get((wh, sku), ())), key=pick_key)


def free(lot):
    return lot.qty - lot.reserved


def sellable_lots(w, wh, sku):
    cat = category_of(sku)
    return [lot for lot in lots_of(w, wh, sku)
            if free(lot) > 0 and cat.sellable(lot.expiry, w.day)]


def available(w, wh, sku):
    return sum(free(lot) for lot in sellable_lots(w, wh, sku))


def free_units(w, wh, sku):
    """Units that are not reserved and not expired."""
    cat = category_of(sku)
    return sum(free(lot) for lot in lots_of(w, wh, sku) if not cat.is_expired(lot.expiry, w.day))


def on_hand(w, wh, sku):
    return sum(lot.qty for lot in lots_of(w, wh, sku))


def total_units(w, wh):
    return sum(lot.qty for lot in w.lots.values() if lot.wh == wh)


def record(w, kind, wh, sku, delta, qty=None, ref=""):
    qty = abs(delta) if qty is None else qty
    w.moves.append(Move(len(w.moves) + 1, w.day, kind, wh, sku, delta, qty, ref))


def new_lot(w, wh, sku, qty, expiry):
    w.lot_seq += 1
    lot = Lot("L%04d" % w.lot_seq, wh, sku, qty, 0, expiry, w.day)
    w.lots[lot.id] = lot
    w.by_slot.setdefault((wh, sku), []).append(lot.id)
    return lot


def remove_lot(w, lot):
    del w.lots[lot.id]
    w.by_slot[(lot.wh, lot.sku)].remove(lot.id)


def reserve(w, wh, sku, qty):
    """Reserve QTY units from the sellable lots, in pick order.  Returns the
    allocations as [wh, lot id, qty] triples."""
    out = []
    left = qty
    for lot in sellable_lots(w, wh, sku):
        if left == 0:
            break
        take = min(free(lot), left)
        lot.reserved += take
        out.append([wh, lot.id, take])
        left -= take
    return out


def release(w, allocs):
    for _, lot_id, qty in allocs:
        w.lots[lot_id].reserved -= qty


def consume(w, allocs, ref):
    """Take reserved units out of stock for a shipment."""
    for wh, lot_id, qty in allocs:
        lot = w.lots[lot_id]
        lot.reserved -= qty
        lot.qty -= qty
        record(w, "ship", wh, lot.sku, -qty, ref=ref)
        if lot.qty == 0:
            remove_lot(w, lot)


def merge_allocs(allocs):
    """Allocations with the same lot added up, in first-seen order."""
    seen = {}
    for wh, lot_id, qty in allocs:
        if lot_id in seen:
            seen[lot_id][2] += qty
        else:
            seen[lot_id] = [wh, lot_id, qty]
    return list(seen.values())
