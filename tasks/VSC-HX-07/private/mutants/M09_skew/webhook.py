# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Webhook outbox.

When a job of a tenant finishes (done, failed or dead) and the tenant has a
``webhook.url``, a delivery is put in the tenant's outbox.  Nothing is sent
anywhere: the outbox is only listed.  Each delivery carries a signature,
the first 16 hex digits of HMAC-SHA256 over the payload keyed with the
tenant's ``webhook.secret`` (``unsigned`` when the secret is empty).  The
signature is derived from the secret but is not the secret, so it is shown.

    webhook list TENANT
    webhook clear TENANT
"""
import hashlib
import hmac

import lexer
from errors import CommandError
from output import kv

OUTBOX_LIMIT = 50


class Delivery:
    __slots__ = ("seq", "at", "url", "payload", "signature")

    def __init__(self, seq, at, url, payload, signature):
        self.seq = seq
        self.at = at
        self.url = url
        self.payload = payload
        self.signature = signature


def sign(secret, payload):
    if not secret:
        return "unsigned"
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]


class Outbox:
    def __init__(self, world):
        self.world = world
        self._boxes = {}
        self._seq = 0
        self.dropped = 0

    def notify(self, tenant, event, fields):
        cfg = self.world.config
        url = cfg.text(tenant, "webhook.url")
        if not url:
            return None
        payload = event + " " + " ".join("%s=%s" % (k, v) for k, v in fields)
        self._seq += 1
        d = Delivery(self._seq, self.world.now, url, payload,
                     sign(cfg.text(tenant, "webhook.secret"), payload))
        box = self._boxes.setdefault(tenant, [])
        box.append(d)
        if len(box) > OUTBOX_LIMIT:
            box.pop(0)
            self.dropped += 1
        return d

    def listing(self, tenant):
        return list(self._boxes.get(tenant, ()))

    def clear(self, tenant):
        return len(self._boxes.pop(tenant, ()))


def cmd_webhook(world, cmd):
    lexer.need(cmd, 3, 3, "webhook list|clear TENANT")
    lexer.allow_opts(cmd, ())
    tenant = world.tenants.require(cmd.words[2]).name
    sub = cmd.words[1]
    if sub == "list":
        box = world.outbox.listing(tenant)
        if not box:
            world.emit("webhook none")
        for d in box:
            world.emit("delivery %d t=%d %s sig=%s %s" % (
                d.seq, d.at, kv("url", d.url), d.signature, kv("payload", d.payload)))
    elif sub == "clear":
        n = world.outbox.clear(tenant)
        world.audit.record(tenant, "webhook.clear", [("deliveries", n)])
        world.emit("webhook cleared %d deliveries of %s" % (n, tenant))
    else:
        raise CommandError("webhook: unknown subcommand %s" % sub)
