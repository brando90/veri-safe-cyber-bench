# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Per-leg view of a journey."""
import units
import windows


def rows(world, ship):
    out = []
    rs = world.store.all(ship.sid)
    count = world.routes.count(ship.route)
    for i in range(count - 1):
        src = world.routes.stop_at(ship.route, i)
        dst = world.routes.stop_at(ship.route, i + 1)
        left = ship.arrival_at(i + 1)
        came = ship.arrival_at(i + 2)
        head = "leg %d %s>%s" % (i + 1, src, dst)
        if left is None or came is None:
            out.append(head + " pending")
            continue
        part = windows.select(rs, left, came)
        mins = (came - left) // units.MIN_MS
        if part:
            avg = units.fmt_tenths(units.div_round_half_up(sum(r.temp for r in part), len(part)))
        else:
            avg = "-"
        out.append("%s depart=%s arrive=%s mins=%d n=%d avg=%s" % (
            head, units.fmt_ms(left), units.fmt_ms(came), mins, len(part), avg))
    return out
