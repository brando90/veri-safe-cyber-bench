# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Bills.

    bill TENANT        one tenant
    bill               every tenant, by name

A bill has three lines (API requests, job runs, egress) priced with the
tenant's current ``price.request`` and ``price.kib`` (millicents), each
line rounded half up to whole cents, and a total that is the sum of the
rounded lines.
"""
import lexer
import units


class Line:
    __slots__ = ("label", "quantity", "unit", "price", "cents")

    def __init__(self, label, quantity, unit, price):
        self.label = label
        self.quantity = quantity
        self.unit = unit
        self.price = price
        self.cents = units.millicents_to_cents(quantity * price)

    def render(self):
        return "  %s %d%s x %dmc = %s" % (self.label, self.quantity, self.unit, self.price,
                                         units.fmt_money(self.cents))


def bill_lines(world, tenant):
    cfg = world.config
    u = world.meter.usage(tenant)
    req_price = cfg.int_value(tenant, "price.request")
    kib_price = cfg.int_value(tenant, "price.kib")
    return [
        Line("api", u.api, "", req_price),
        Line("jobs", u.jobs, "", req_price),
        Line("egress", units.kib_ceil(u.egress_bytes), "KiB", kib_price),
    ]


def render_bill(world, tenant):
    t = world.tenants.require(tenant)
    lines = bill_lines(world, tenant)
    world.emit("bill %s plan=%s" % (t.name, t.plan))
    for line in lines:
        world.emit(line.render())
    world.emit("  total %s" % units.fmt_money(sum(line.cents for line in lines)))


def cmd_bill(world, cmd):
    lexer.need(cmd, 1, 2, "bill [TENANT]")
    lexer.allow_opts(cmd, ())
    if len(cmd.words) == 2:
        render_bill(world, cmd.words[1])
        return
    tenants = world.tenants.all()
    if not tenants:
        world.emit("bill none")
    for t in tenants:
        render_bill(world, t.name)
