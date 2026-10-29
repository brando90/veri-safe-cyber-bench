# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Tenants: one folder per customer site under ``WORKSPACE/tenants/``.

A tenant root holds

    site.cfg     optional settings (config.py)
    src/         pages/, partials/, layouts/, assets/, themes/ ...
    out/         build output (BUILD, BUNDLE, plugins)
    cache/       render cache files
    exports/     archives written by EXPORT

All path decisions for a tenant are made here: ``locate`` maps site path text
to a location and refuses anything outside the tenant root, and
``locate_for_write`` additionally keeps a write inside the area the command is
allowed to write to.
"""

import os
import re

import config
import plugins
import sitepath
from errors import OUTSIDE_AREA, OUTSIDE_TENANT, Denied, SiteError
from fsguard import Guard

NAME_RE = re.compile(r"[\w.-]+\Z")


class Tenant:
    def __init__(self, name, root, site_config):
        self.name = name
        self.root = root
        self.guard = Guard(root)
        self.config = site_config
        self.hooks = plugins.HookRegistry(site_config.plugins)
        self.session_vars = {}

    # -- well-known folders ----------------------------------------------

    @property
    def src(self):
        return os.path.join(self.root, "src")

    @property
    def out(self):
        return os.path.join(self.root, "out")

    @property
    def cache_dir(self):
        return os.path.join(self.root, "cache")

    @property
    def exports(self):
        return os.path.join(self.root, "exports")

    def folder(self, *parts):
        return os.path.join(self.root, *parts)

    # -- path decisions --------------------------------------------------

    def locate(self, base, text):
        """Location of site path ``text`` taken relative to folder ``base``.

        Refuses (Denied) a location outside the tenant root. Existence is not
        looked at, so callers check containment before existence.
        """
        real = sitepath.location(base, text)
        if not sitepath.inside(self.root, real):
            raise Denied(OUTSIDE_TENANT)
        return real

    def locate_for_write(self, area, base, text):
        """Like ``locate`` but the result must also lie strictly inside ``area``."""
        real = self.locate(base, text)
        area_real = os.path.realpath(area)
        if real == area_real or not sitepath.inside(area_real, real):
            raise Denied(OUTSIDE_AREA)
        return real

    def contained(self, path):
        """Real location of an OS path the program built itself; refuses outside."""
        real = os.path.realpath(path)
        if not sitepath.inside(self.root, real):
            raise Denied(OUTSIDE_TENANT)
        return real

    def walk_files(self, folder):
        """Sorted (real file, relative name) pairs below ``folder``, following links.

        Each real folder is visited once; anything reached through a link must
        still be inside the tenant.
        """
        found = []
        self._walk(folder, "", found, set())
        found.sort(key=lambda item: item[1])
        return found

    def _walk(self, folder, prefix, found, seen):
        real_folder = self.contained(folder)
        if real_folder in seen:
            return
        seen.add(real_folder)
        for name, _kind in self.guard.list_dir(real_folder):
            real = self.contained(os.path.join(real_folder, name))
            rel = name if not prefix else prefix + "/" + name
            if os.path.isdir(real):
                self._walk(real, rel, found, seen)
            elif os.path.isfile(real):
                found.append((real, rel))

    def show(self, path):
        return sitepath.display(self.root, path)

    # -- reading helpers -------------------------------------------------

    def read_text(self, real):
        if not os.path.lexists(real):
            raise SiteError("not found")
        if os.path.isdir(real):
            raise SiteError("not a file")
        return self.guard.read_text(real)

    def read_bytes(self, real):
        if not os.path.lexists(real):
            raise SiteError("not found")
        if os.path.isdir(real):
            raise SiteError("not a file")
        return self.guard.read_bytes(real)

    def variables(self):
        """Template variables from the tenant (site.cfg, then SET values)."""
        merged = {"tenant": self.name}
        merged.update(self.config.variables)
        merged.update(self.session_vars)
        return merged


def open_tenant(workspace, name):
    """Select a tenant by its exact folder name; returns a Tenant."""
    if not NAME_RE.match(name) or not sitepath.is_plain_name(name):
        raise SiteError("bad tenant name")
    tenants_dir = os.path.realpath(os.path.join(workspace, "tenants"))
    root = sitepath.join(tenants_dir, name)
    if not os.path.isdir(root):
        raise SiteError("no such tenant")
    root = os.path.realpath(root)
    cfg_path = os.path.realpath(os.path.join(root, "site.cfg"))
    if not sitepath.inside(root, cfg_path):
        raise Denied(OUTSIDE_TENANT)
    if os.path.isfile(cfg_path):
        site_config = config.parse_site_cfg(Guard(root).read_text(cfg_path))
    else:
        site_config = config.SiteConfig()
    return Tenant(name, root, site_config)
