# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The simulated upstream service.

Every handler is deterministic: the response depends only on the route, the
calling tenant/key, the ``q.`` parameters and (for reports) the attempt
number.  ``nbytes`` is the simulated payload size; the body is a short
summary line that the gateway prints.
"""
import units
from errors import CommandError

MAX_BLOB = units.MIB
REPORT_BYTES = 1500
ITEM_BYTES = 120


class Response:
    __slots__ = ("status", "body", "nbytes")

    def __init__(self, status, body, nbytes):
        self.status = status
        self.body = body
        self.nbytes = nbytes


NOT_FOUND = Response(404, "not found", 9)


def bad_request(why):
    return Response(400, "bad request: " + why, 12 + len(why))


class Backend:
    def __init__(self, world):
        self.world = world
        self.calls = 0

    def call(self, ctx, route):
        self.calls += 1
        if route is None:
            return NOT_FOUND
        handler = getattr(self, "h_" + route.handler)
        try:
            return handler(ctx)
        except CommandError as exc:
            return bad_request(str(exc))

    def h_catalog(self, ctx):
        return Response(200, "catalog items=12 rev=3", 2048)

    def h_me(self, ctx):
        key = self.world.keys.get(ctx.tenant, ctx.keyid)
        label = key.label if key is not None and key.label else "-"
        return Response(200, "me tenant=%s key=%s label=%s" % (ctx.tenant, ctx.keyid, label), 256)

    def h_items_list(self, ctx):
        n = units.parse_int(ctx.params.get("n", "5"), "n", lo=1, hi=100)
        return Response(200, "items tenant=%s n=%d" % (ctx.tenant, n), ITEM_BYTES * n)

    def h_items_create(self, ctx):
        return Response(201, "created tenant=%s" % ctx.tenant, 64)

    def h_blob(self, ctx):
        size = units.parse_size(ctx.params.get("size", "1KiB"), "size")
        if size > MAX_BLOB:
            raise CommandError("size above 1MiB")
        return Response(200, "blob tenant=%s size=%d" % (ctx.tenant, size), size)

    def h_report(self, ctx):
        fail = units.parse_int(ctx.params.get("fail", "0"), "fail", lo=0, hi=20)
        if ctx.attempt <= fail:
            return Response(503, "unavailable", 11)
        return Response(200, "report tenant=%s attempt=%d" % (ctx.tenant, ctx.attempt), REPORT_BYTES)
