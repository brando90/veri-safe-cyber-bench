# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Command handlers for a sitesmith session.

One command per line. Command words are case-insensitive; arguments are
separated by whitespace (SET and ECHO take the rest of the line). Each
handler returns the lines to print; failures are raised as SiteError or
Denied and printed by ``Session.execute``.
"""

import os
import sys

import archive
import builder
import bundler
import config
import tenants
from assets import url_for
from cache import Deps, RenderCache
from errors import SiteError

USAGE = {
    "TENANT": "TENANT name",
    "SET": "SET name value",
    "VARS": "VARS",
    "RENDER": "RENDER page",
    "BUILD": "BUILD",
    "BUNDLE": "BUNDLE name file...",
    "ASSET": "ASSET name",
    "CAT": "CAT path",
    "LS": "LS [path]",
    "EXPORT": "EXPORT name",
    "TOC": "TOC name",
    "IMPORT": "IMPORT archive theme",
    "STATS": "STATS",
    "PLUGINS": "PLUGINS",
    "CLEAN": "CLEAN",
    "ECHO": "ECHO text",
}

KIND_SUFFIX = {"dir": "/", "link": "@", "file": ""}


def emit(text):
    sys.stdout.write(text + "\n")


def text_lines(text):
    """Lines of a file or rendered page as printed (no trailing empty line)."""
    if not text:
        return []
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n")


class Session:
    def __init__(self, workspace):
        self.workspace = workspace
        self.tenant = None
        self.render_cache = RenderCache()

    def execute(self, line):
        """Run one line; returns its status (0, 2 or 4)."""
        text = line.strip()
        if not text or text.startswith("#"):
            return 0
        word, _, rest = text.partition(" ")
        word = word.upper()
        handler = self.HANDLERS.get(word)
        try:
            if handler is None:
                raise SiteError("unknown command")
            for out in handler(self, rest.strip(), rest.split()):
                emit(out)
            return 0
        except SiteError as exc:
            emit("%s: %s" % (exc.prefix, exc.reason))
            return exc.status

    # -- helpers ------------------------------------------------------------

    def _need(self):
        if self.tenant is None:
            raise SiteError("no tenant selected")
        return self.tenant

    @staticmethod
    def _arity(word, args, low, high):
        if len(args) < low or (high is not None and len(args) > high):
            raise SiteError("usage: " + USAGE[word])

    # -- commands -----------------------------------------------------------

    def cmd_tenant(self, rest, args):
        self._arity("TENANT", args, 1, 1)
        self.tenant = None
        self.tenant = tenants.open_tenant(self.workspace, args[0])
        return ["OK tenant " + args[0]]

    def cmd_set(self, rest, args):
        self._arity("SET", args, 1, None)
        tenant = self._need()
        name, _, value = rest.partition(" ")
        if not config.VAR_NAME.match(name):
            raise SiteError("bad variable name")
        tenant.session_vars[name] = value.strip()
        return ["OK set " + name]

    def cmd_vars(self, rest, args):
        self._arity("VARS", args, 0, 0)
        variables = self._need().variables()
        return ["%s = %s" % item for item in sorted(variables.items())]

    def cmd_render(self, rest, args):
        self._arity("RENDER", args, 1, 1)
        return text_lines(builder.render_one(self._need(), args[0]))

    def cmd_build(self, rest, args):
        self._arity("BUILD", args, 0, 0)
        return builder.build(self._need(), self.render_cache)

    def cmd_bundle(self, rest, args):
        self._arity("BUNDLE", args, 2, None)
        files, size, shown = bundler.bundle(self._need(), args[0], args[1:])
        return ["BUNDLED %s: %d files, %d bytes" % (shown, files, size)]

    def cmd_asset(self, rest, args):
        self._arity("ASSET", args, 1, 1)
        return [url_for(self._need(), args[0], Deps())]

    def cmd_cat(self, rest, args):
        self._arity("CAT", args, 1, 1)
        tenant = self._need()
        real = tenant.locate(tenant.root, args[0])
        return text_lines(tenant.read_text(real))

    def cmd_ls(self, rest, args):
        self._arity("LS", args, 0, 1)
        tenant = self._need()
        real = tenant.locate(tenant.root, args[0] if args else ".")
        if not os.path.lexists(real):
            raise SiteError("not found")
        if not os.path.isdir(real):
            raise SiteError("not a folder")
        entries = tenant.guard.list_dir(real)
        if not entries:
            return ["(empty)"]
        return [name + KIND_SUFFIX[kind] for name, kind in entries]

    def cmd_export(self, rest, args):
        self._arity("EXPORT", args, 1, 1)
        count, size = archive.export(self._need(), args[0])
        return ["EXPORTED %s: %d files, %d bytes" % (args[0], count, size)]

    def cmd_toc(self, rest, args):
        self._arity("TOC", args, 1, 1)
        members = archive.toc(self._need(), args[0])
        lines = ["%s %d" % (name, size) for name, size in members]
        lines.append("TOC %s: %d files" % (args[0], len(members)))
        return lines

    def cmd_import(self, rest, args):
        self._arity("IMPORT", args, 2, 2)
        count = archive.import_archive(self._need(), args[0], args[1])
        return ["IMPORTED %s: %d files" % (args[1], count)]

    def cmd_stats(self, rest, args):
        self._arity("STATS", args, 0, 0)
        hits, misses, entries = self.render_cache.stats(self._need())
        return ["cache: %d hits, %d misses, %d entries" % (hits, misses, entries)]

    def cmd_plugins(self, rest, args):
        self._arity("PLUGINS", args, 0, 0)
        return self._need().hooks.describe() or ["(none)"]

    def cmd_clean(self, rest, args):
        self._arity("CLEAN", args, 0, 0)
        tenant = self._need()
        removed = 0
        for area in (tenant.out, tenant.cache_dir):
            if os.path.lexists(area):
                removed += _clear(tenant, tenant.contained(area))
        self.render_cache.forget(tenant)
        return ["CLEANED %d files" % removed]

    def cmd_echo(self, rest, args):
        return [rest]

    HANDLERS = {
        "TENANT": cmd_tenant,
        "SET": cmd_set,
        "VARS": cmd_vars,
        "RENDER": cmd_render,
        "BUILD": cmd_build,
        "BUNDLE": cmd_bundle,
        "ASSET": cmd_asset,
        "CAT": cmd_cat,
        "LS": cmd_ls,
        "EXPORT": cmd_export,
        "TOC": cmd_toc,
        "IMPORT": cmd_import,
        "STATS": cmd_stats,
        "PLUGINS": cmd_plugins,
        "CLEAN": cmd_clean,
        "ECHO": cmd_echo,
    }


def _clear(tenant, folder):
    """Remove every file and link below ``folder`` (links are not followed)."""
    if not os.path.isdir(folder):
        return 0
    removed = 0
    for name, kind in tenant.guard.list_dir(folder):
        path = os.path.join(folder, name)
        if kind == "dir":
            removed += _clear(tenant, path)
            tenant.guard.remove_empty_dir(path)
        else:
            tenant.guard.remove_entry(path)
            removed += 1
    return removed
