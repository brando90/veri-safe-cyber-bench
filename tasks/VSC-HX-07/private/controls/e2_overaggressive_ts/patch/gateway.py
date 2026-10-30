# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The request pipeline.

    req CRED METHOD PATH [nonce=N ts=S] [q.NAME=VALUE ...]

Stages, in this order (README.md, "Admission"):

  1. authentication of the credential            -> deny auth ...
  2. replay protection (freshness, then nonce)   -> deny nonce-required|stale|replay
  3. rate limit                                  -> deny rate [retry_after=N]
  4. request quota                               -> deny quota-requests
  5. cache lookup or upstream call
  6. egress quota on the response size           -> deny quota-egress

Stages only look.  Each returns what it would record and the gateway
applies all of it in one step once the request is accepted (``_commit``),
so a refused request leaves no trace except its audit record.
"""
import backend
import cachekey
import invariant
import lexer
import nonce as nonce_mod
import redact
import routes
from errors import CommandError, Deny


class Ctx:
    """Everything known about one request or job run."""

    __slots__ = ("kind", "line", "now", "tenant", "keyid", "method", "path", "params",
                 "nonce", "ts", "attempt")

    def __init__(self, kind, line, now):
        self.kind = kind
        self.line = line
        self.now = now
        self.tenant = None
        self.keyid = None
        self.method = "GET"
        self.path = None
        self.params = {}
        self.nonce = None
        self.ts = None
        self.attempt = 1


def parse_request(cmd):
    lexer.need(cmd, 4, 4, "req CRED METHOD PATH [nonce=N ts=S] [q.NAME=VALUE ...]")
    lexer.allow_opts(cmd, ("nonce", "ts"), prefixes=("q.",))
    cred, method, path = cmd.words[1], cmd.words[2], cmd.words[3]
    if method not in ("GET", "POST"):
        raise CommandError("req: method must be GET or POST")
    if not routes.valid_path(path):
        raise CommandError("req: bad path")
    has_nonce, has_ts = "nonce" in cmd.opts, "ts" in cmd.opts
    if has_nonce != has_ts:
        raise CommandError("req: nonce= and ts= go together")
    nonce = nonce_mod.parse_nonce(cmd.opts["nonce"]) if has_nonce else None
    ts = nonce_mod.parse_ts(cmd.opts["ts"]) if has_ts else None
    params = cmd.prefixed("q.")
    for name, value in params.items():
        if len(value) > 64:
            raise CommandError("req: parameter %s longer than 64 characters" % name)
    return cred, method, routes.normalise(path), nonce, ts, params


class Gateway:
    def __init__(self, world):
        self.world = world
        self.served = 0
        self.refused = 0

    # ------------------------------------------------------------ cache helpers
    def cache_ttl(self, route, tenant):
        cfg = self.world.config
        if route.cache == "shared":
            return cfg.duration_ms(None, "cache.ttl")
        return cfg.duration_ms(tenant, "cache.ttl")

    def cacheable(self, ctx, route):
        return (route is not None and ctx.method == "GET" and route.cache != "none"
                and self.cache_ttl(route, ctx.tenant) > 0)

    # ------------------------------------------------------------ pipeline
    def handle(self, cmd):
        w = self.world
        cred, method, path, nonce, ts, params = parse_request(cmd)
        ctx = Ctx("api", cmd.line, w.now)
        ctx.method, ctx.path, ctx.params, ctx.nonce, ctx.ts = method, path, params, nonce, ts
        parts = redact.split_credential(cred)
        audit_tenant = parts[0] if parts and w.tenants.get(parts[0]) else None
        try:
            key = w.keys.authenticate(cred, ctx.now)
            ctx.tenant, ctx.keyid = key.tenant, key.keyid
            pending = [w.nonces.check(ctx), w.limiter.check(ctx)]
            w.quota.check_requests(ctx)
            route = routes.match(method, path)
            resp, source, ckey = self._fetch(ctx, route)
            w.quota.check_egress(ctx, resp.nbytes)
        except Deny as deny:
            self.refused += 1
            w.audit.record(audit_tenant, "req", [("line", cmd.line), ("result", "deny:" + deny.code)])
            w.emit(deny.line())
            return
        self._commit(ctx, pending, route, resp, source, ckey)
        w.audit.record(ctx.tenant, "req", [
            ("line", cmd.line), ("result", "ok:%d:%s" % (resp.status, source))])
        w.emit("ok %d %s %dB %s" % (resp.status, source, resp.nbytes, resp.body))

    def _fetch(self, ctx, route):
        """(response, source, cache key) where source is hit, miss or off."""
        w = self.world
        if not self.cacheable(ctx, route):
            return w.backend.call(ctx, route), "off", None
        params = dict(ctx.params)
        if ctx.nonce is not None:
            params["nonce"] = ctx.nonce
        ckey = cachekey.build(cachekey.scope(route, ctx), ctx.method, route.path, params)
        entry = w.cache.get(ckey, ctx.now)
        if entry is not None:
            return backend.Response(entry.status, entry.body, entry.nbytes), "hit", ckey
        return w.backend.call(ctx, route), "miss", ckey

    def _commit(self, ctx, pending, route, resp, source, ckey):
        w = self.world
        for apply in pending:
            if apply is not None:
                apply()
        w.quota.commit(ctx.tenant, resp.nbytes)
        w.meter.record(ctx.tenant, "api", resp.nbytes)
        if source == "miss" and resp.status == 200:
            w.cache.put(ckey, ctx.tenant if route.cache != "shared" else None, route.path, resp,
                        ctx.now, self.cache_ttl(route, ctx.tenant))
        if route is not None and ctx.method == "POST":
            w.cache.purge(ctx.tenant, route.path)
        self.served += 1
        invariant.after_commit(w, ctx)


def cmd_req(world, cmd):
    world.gateway.handle(cmd)
