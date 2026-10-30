# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""API keys.

A key is identified by (tenant, keyid); key ids are chosen by the tenant and
are unique within that tenant only, so two tenants may both have a key
called ``main``.  A client presents the credential ``TENANT.KEYID.SECRET``.

A key issued at time T with ``ttl=D`` is valid while now < T + D; without a
ttl it never expires.  A revoked key stays listed but never authenticates
again.  ``rotate`` replaces the secret and keeps everything else.
"""
import hmac
import re

import lexer
import redact
import timeutil
import units
from errors import CommandError, Deny
from output import kv

KEYID_RE = re.compile(redact.KEYID_PATTERN + r"\Z")
SECRET_RE = re.compile(r"[A-Za-z0-9_-]{8,64}\Z")
LABEL_MAX = 40


class ApiKey:
    __slots__ = ("tenant", "keyid", "secret", "issued", "expires_at", "label", "revoked_at")

    def __init__(self, tenant, keyid, secret, issued, expires_at, label):
        self.tenant = tenant
        self.keyid = keyid
        self.secret = secret
        self.issued = issued
        self.expires_at = expires_at
        self.label = label
        self.revoked_at = None

    @property
    def ident(self):
        return "%s.%s" % (self.tenant, self.keyid)

    def state(self, now):
        if self.revoked_at is not None:
            return "revoked"
        if timeutil.expired(now, self.expires_at):
            return "expired"
        return "active"


def check_secret(secret):
    if not SECRET_RE.match(secret):
        raise CommandError("key: secret must be 8 to 64 characters from A-Z a-z 0-9 _ -")


class KeyStore:
    def __init__(self, world):
        self.world = world
        self._keys = {}

    def get(self, tenant, keyid):
        return self._keys.get((tenant, keyid))

    def require(self, tenant, keyid):
        self.world.tenants.require(tenant)
        key = self._keys.get((tenant, keyid))
        if key is None:
            raise CommandError("key: unknown key %s.%s" % (tenant, keyid))
        return key

    def for_tenant(self, tenant):
        return [self._keys[k] for k in sorted(self._keys) if k[0] == tenant]

    def issue(self, tenant, keyid, secret, ttl, label):
        self.world.tenants.require(tenant)
        if not KEYID_RE.match(keyid):
            raise CommandError("key: bad key id %s" % keyid)
        if (tenant, keyid) in self._keys:
            raise CommandError("key: %s.%s already exists" % (tenant, keyid))
        check_secret(secret)
        if len(label) > LABEL_MAX:
            raise CommandError("key: label longer than %d characters" % LABEL_MAX)
        now = self.world.now
        expires = None if ttl is None else timeutil.deadline_after(now, ttl)
        key = ApiKey(tenant, keyid, secret, now, expires, label)
        self._keys[(tenant, keyid)] = key
        self.world.audit.record(tenant, "key.issue", [
            ("key", keyid), ("expires", timeutil.fmt_deadline(expires)), ("label", label)])
        return key

    def revoke(self, tenant, keyid):
        key = self.require(tenant, keyid)
        if key.revoked_at is None:
            key.revoked_at = self.world.now
        self.world.audit.record(tenant, "key.revoke", [("key", keyid)])
        return key

    def rotate(self, tenant, keyid, secret):
        key = self.require(tenant, keyid)
        if key.state(self.world.now) != "active":
            raise CommandError("key: %s is %s" % (key.ident, key.state(self.world.now)))
        check_secret(secret)
        key.secret = secret
        self.world.audit.record(tenant, "key.rotate", [("key", keyid)])
        return key

    def authenticate(self, cred, now):
        """The ApiKey for credential CRED, or Deny('auth', ...)."""
        parts = redact.split_credential(cred)
        if parts is None:
            raise Deny("auth", "malformed cred=" + redact.MALFORMED)
        tenant, keyid, secret = parts
        shown = "cred=" + redact.mask_credential(cred)
        owner = self.world.tenants.get(tenant)
        if owner is None:
            raise Deny("auth", "unknown-tenant " + shown)
        key = self._keys.get((tenant, keyid))
        if key is None:
            raise Deny("auth", "unknown-key " + shown)
        if not hmac.compare_digest(key.secret.encode(), secret.encode()):
            raise Deny("auth", "bad-secret " + shown)
        state = key.state(now)
        if state != "active":
            raise Deny("auth", state + " " + shown)
        if owner.suspended:
            raise Deny("auth", "suspended " + shown)
        return key


def cmd_key(world, cmd):
    if len(cmd.words) < 2:
        raise CommandError("usage: key issue|revoke|rotate|show|list ...")
    sub = cmd.words[1]
    store = world.keys
    if sub == "issue":
        lexer.need(cmd, 4, 4, "key issue TENANT KEYID secret=SECRET [ttl=DURATION] [label=TEXT]")
        lexer.allow_opts(cmd, ("secret", "ttl", "label"))
        if "secret" not in cmd.opts:
            raise CommandError("key issue: secret= is required")
        ttl = cmd.opt("ttl")
        ttl = None if ttl is None else units.parse_duration(ttl, "ttl")
        if ttl is not None and ttl <= 0:
            raise CommandError("key issue: ttl must be positive")
        key = store.issue(cmd.words[2], cmd.words[3], cmd.opts["secret"], ttl, cmd.opt("label", ""))
        world.emit("key %s issued expires=%s" % (key.ident, timeutil.fmt_deadline(key.expires_at)))
    elif sub == "revoke":
        lexer.need(cmd, 4, 4, "key revoke TENANT KEYID")
        lexer.allow_opts(cmd, ())
        key = store.revoke(cmd.words[2], cmd.words[3])
        world.emit("key %s revoked" % key.ident)
    elif sub == "rotate":
        lexer.need(cmd, 4, 4, "key rotate TENANT KEYID secret=SECRET")
        lexer.allow_opts(cmd, ("secret",))
        if "secret" not in cmd.opts:
            raise CommandError("key rotate: secret= is required")
        key = store.rotate(cmd.words[2], cmd.words[3], cmd.opts["secret"])
        world.emit("key %s rotated" % key.ident)
    elif sub == "show":
        lexer.need(cmd, 4, 4, "key show TENANT KEYID")
        lexer.allow_opts(cmd, ())
        import admin
        admin.key_show(world, cmd.words[2], cmd.words[3])
    elif sub == "list":
        lexer.need(cmd, 3, 3, "key list TENANT")
        lexer.allow_opts(cmd, ())
        tenant = world.tenants.require(cmd.words[2]).name
        keys = store.for_tenant(tenant)
        if not keys:
            world.emit("keys none")
        for key in keys:
            world.emit("key %s %s expires=%s %s" % (
                key.ident, key.state(world.now), timeutil.fmt_deadline(key.expires_at),
                kv("label", key.label)))
    else:
        raise CommandError("key: unknown subcommand %s" % sub)
