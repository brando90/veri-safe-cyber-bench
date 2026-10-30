# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Layered configuration.

Layers, from strongest to weakest: ``tenant:NAME``, ``plan:PLAN`` (the plan
the tenant is on), ``default``.  The effective value of a setting for a
tenant is the value in the strongest layer that has it.  Global settings
(``cache.capacity``) live only in the default layer.

Values are validated and stored in canonical text form (``90s`` -> ``90s``,
``90000`` -> ``90s``, ``2048`` -> ``2KiB``).  Each layer carries a version
number that is bumped on every change; components that keep derived copies
of settings compare a *stamp* (see ``Config.stamp``) to know when to reload.
"""
import lexer
import plans
import redact
import units
from errors import CommandError
from output import kv


class Setting:
    def __init__(self, name, kind, lo=None, hi=None, choices=None, scope="tenant"):
        self.name = name
        self.kind = kind
        self.lo = lo
        self.hi = hi
        self.choices = choices
        self.scope = scope

    def canonical(self, text):
        """Validate TEXT and return the canonical stored form."""
        name = self.name
        if self.kind == "int":
            return str(units.parse_int(text, name, self.lo, self.hi))
        if self.kind == "duration":
            ms = units.parse_duration(text, name)
            self._range(ms, units.fmt_duration)
            return units.fmt_duration(ms)
        if self.kind == "size":
            nbytes = units.parse_size(text, name)
            self._range(nbytes, units.fmt_size)
            return units.fmt_size(nbytes)
        if self.kind == "flag":
            return "on" if units.parse_flag(text, name) else "off"
        if self.kind == "choice":
            if text not in self.choices:
                raise CommandError("bad %s %s (expected %s)" % (name, text, " or ".join(self.choices)))
            return text
        if len(text) > 128 or any(ord(c) < 32 for c in text):
            raise CommandError("bad %s (at most 128 printable characters)" % name)
        return text

    def _range(self, value, fmt):
        if self.lo is not None and value < self.lo:
            raise CommandError("%s must be at least %s" % (self.name, fmt(self.lo)))
        if self.hi is not None and value > self.hi:
            raise CommandError("%s must be at most %s" % (self.name, fmt(self.hi)))

    def parse(self, stored):
        """Typed value of a canonical stored text."""
        if self.kind == "int":
            return int(stored)
        if self.kind == "duration":
            return units.parse_duration(stored)
        if self.kind == "size":
            return units.parse_size(stored)
        if self.kind == "flag":
            return stored == "on"
        return stored


SCHEMA = {s.name: s for s in (
    Setting("rate.mode", "choice", choices=("fixed", "sliding")),
    Setting("rate.limit", "int", lo=0, hi=1000000),
    Setting("rate.window", "duration", lo=1, hi=units.HOUR),
    Setting("quota.requests", "int", lo=0, hi=10 ** 9),
    Setting("quota.egress", "size", lo=0, hi=1 << 40),
    Setting("quota.period", "duration", lo=units.SECOND, hi=30 * units.DAY),
    Setting("cache.ttl", "duration", lo=0, hi=units.DAY),
    Setting("cache.capacity", "size", lo=0, hi=64 * units.MIB, scope="global"),
    Setting("replay.window", "duration", lo=units.SECOND, hi=units.DAY),
    Setting("replay.skew", "duration", lo=0, hi=units.HOUR),
    Setting("replay.required", "flag"),
    Setting("jobs.max_attempts", "int", lo=1, hi=10),
    Setting("jobs.backoff", "duration", lo=1, hi=units.HOUR),
    Setting("price.request", "int", lo=0, hi=1000000),
    Setting("price.kib", "int", lo=0, hi=1000000),
    Setting("backend.token", "text"),
    Setting("webhook.url", "text"),
    Setting("webhook.secret", "text"),
)}


class Config:
    def __init__(self, world):
        self.world = world
        self.layers = {"default": {}}
        for name, text in plans.BASE.items():
            self.layers["default"][name] = SCHEMA[name].canonical(text)
        for pname, plan in plans.PLANS.items():
            self.layers["plan:" + pname] = {
                name: SCHEMA[name].canonical(text) for name, text in plan.overrides.items()}
        self.versions = {layer: 1 for layer in self.layers}

    # ------------------------------------------------------------ layers
    def chain(self, tenant):
        """Layer names consulted for TENANT, strongest first (None: default only)."""
        if tenant is None:
            return ["default"]
        t = self.world.tenants.require(tenant)
        return ["tenant:" + tenant, "plan:" + t.plan, "default"]

    def check_layer(self, layer):
        if layer == "default":
            return None
        kind, _, rest = layer.partition(":")
        if kind == "plan" and rest in plans.PLANS:
            return None
        if kind == "tenant":
            self.world.tenants.require(rest)
            return rest
        raise CommandError("config: unknown layer %s" % layer)

    def lookup(self, tenant, name):
        """(stored text, layer) of the effective value of NAME for TENANT."""
        setting = SCHEMA.get(name)
        if setting is None:
            raise CommandError("config: unknown setting %s" % name)
        chain = ["default"] if setting.scope == "global" else self.chain(tenant)
        for layer in chain:
            values = self.layers.get(layer)
            if values is not None and name in values:
                return values[name], layer
        raise CommandError("config: %s has no value" % name)

    def stamp(self, tenant):
        """Changes whenever any layer that feeds TENANT's settings changes."""
        t = self.world.tenants.require(tenant)
        return (self.versions["default"], t.plan, self.versions.get("plan:" + t.plan, 0),
                self.versions.get("tenant:" + tenant, 0))

    # ------------------------------------------------------------ typed access
    def value(self, tenant, name):
        text, _ = self.lookup(tenant, name)
        return SCHEMA[name].parse(text)

    def duration_ms(self, tenant, name):
        return self.value(tenant, name)

    def size_bytes(self, tenant, name):
        return self.value(tenant, name)

    def int_value(self, tenant, name):
        return self.value(tenant, name)

    def flag(self, tenant, name):
        return self.value(tenant, name)

    def text(self, tenant, name):
        return self.value(tenant, name)

    def seconds(self, tenant, name):
        """Legacy accessor: a duration setting in whole seconds (truncated)."""
        return self.value(tenant, name) // units.SECOND

    # ------------------------------------------------------------ changes
    def set(self, layer, name, text):
        tenant = self.check_layer(layer)
        setting = SCHEMA.get(name)
        if setting is None:
            raise CommandError("config: unknown setting %s" % name)
        if setting.scope == "global" and layer != "default":
            raise CommandError("config: %s can only be set on the default layer" % name)
        stored = setting.canonical(text)
        self.layers.setdefault(layer, {})[name] = stored
        self.versions[layer] = self.versions.get(layer, 0) + 1
        self.world.audit.record(tenant, "config.set", [
            ("layer", layer), ("name", name), ("value", redact.show_value(name, stored))])
        return stored

    def load(self, layer, pairs):
        """Set several settings on one layer: all are validated first, and
        nothing changes unless every one of them is valid."""
        self.check_layer(layer)
        checked = []
        for name in sorted(pairs):
            setting = SCHEMA.get(name)
            if setting is None:
                raise CommandError("config: unknown setting %s" % name)
            if setting.scope == "global" and layer != "default":
                raise CommandError("config: %s can only be set on the default layer" % name)
            checked.append((name, setting.canonical(pairs[name])))
        return [(name, self.set(layer, name, stored)) for name, stored in checked]

    def unset(self, layer, name):
        tenant = self.check_layer(layer)
        if name not in SCHEMA:
            raise CommandError("config: unknown setting %s" % name)
        if layer == "default":
            raise CommandError("config: default values cannot be removed")
        values = self.layers.get(layer, {})
        if name not in values:
            raise CommandError("config: %s is not set on %s" % (name, layer))
        del values[name]
        self.versions[layer] = self.versions.get(layer, 0) + 1
        self.world.audit.record(tenant, "config.unset", [("layer", layer), ("name", name)])

    def drop_tenant_layer(self, tenant):
        layer = "tenant:" + tenant
        if self.layers.pop(layer, None) is not None:
            self.versions[layer] = self.versions.get(layer, 0) + 1


def _line(name, stored, layer):
    return "%s (%s)" % (kv(name, redact.show_value(name, stored)), layer)


def cmd_config(world, cmd):
    if len(cmd.words) < 2:
        raise CommandError("usage: config set|load|unset|get|show|explain|layers ...")
    cfg = world.config
    sub = cmd.words[1]
    if sub == "load":
        lexer.need(cmd, 3, 3, "config load LAYER NAME=VALUE ...")
        if not cmd.opts:
            raise CommandError("config load: nothing to load")
        for name, stored in cfg.load(cmd.words[2], dict(cmd.opts)):
            world.emit("config %s %s" % (cmd.words[2], kv(name, redact.show_value(name, stored))))
        return
    lexer.allow_opts(cmd, ())
    if sub == "set":
        lexer.need(cmd, 5, 5, "config set LAYER NAME VALUE")
        layer, name = cmd.words[2], cmd.words[3]
        stored = cfg.set(layer, name, cmd.words[4])
        world.emit("config %s %s" % (layer, kv(name, redact.show_value(name, stored))))
    elif sub == "unset":
        lexer.need(cmd, 4, 4, "config unset LAYER NAME")
        cfg.unset(cmd.words[2], cmd.words[3])
        world.emit("config %s %s unset" % (cmd.words[2], cmd.words[3]))
    elif sub == "get":
        lexer.need(cmd, 4, 4, "config get TENANT NAME")
        tenant = world.tenants.require(cmd.words[2]).name
        stored, layer = cfg.lookup(tenant, cmd.words[3])
        world.emit(_line(cmd.words[3], stored, layer))
    elif sub == "show":
        lexer.need(cmd, 3, 3, "config show TENANT")
        tenant = world.tenants.require(cmd.words[2]).name
        for name in sorted(SCHEMA):
            stored, layer = cfg.lookup(tenant, name)
            world.emit(_line(name, stored, layer))
    elif sub == "explain":
        lexer.need(cmd, 4, 4, "config explain TENANT NAME")
        tenant = world.tenants.require(cmd.words[2]).name
        name = cmd.words[3]
        stored, winner = cfg.lookup(tenant, name)
        chain = ["default"] if SCHEMA[name].scope == "global" else cfg.chain(tenant)
        for layer in chain:
            values = cfg.layers.get(layer, {})
            if name in values:
                mark = "*" if layer == winner else " "
                world.emit("%s %s %s" % (mark, layer, kv(name, redact.show_value(name, values[name]))))
            else:
                world.emit("  %s (not set)" % layer)
    elif sub == "layers":
        lexer.need(cmd, 2, 2, "config layers")
        for layer in sorted(cfg.layers):
            world.emit("layer %s settings=%d version=%d" % (
                layer, len(cfg.layers[layer]), cfg.versions.get(layer, 0)))
    else:
        raise CommandError("config: unknown subcommand %s" % sub)
