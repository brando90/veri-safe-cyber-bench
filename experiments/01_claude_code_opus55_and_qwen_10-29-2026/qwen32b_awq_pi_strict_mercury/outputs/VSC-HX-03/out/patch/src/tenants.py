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

    def locate(self, base, text):
        real = sitepath.location(base, text)
        if not sitepath.inside(self.root, real):
            raise Denied(OUTSIDE_TENANT)
        # Ensure reads are confined to allowed areas
        if not self._is_allowed_area(real, 'read'):
            raise Denied(OUTSIDE_AREA)
        return real

    def locate_for_write(self, area, base, text):
        real = self.locate(base, text)
        area_real = os.path.realpath(area)
        if real == area_real or not sitepath.inside(area_real, real):
            raise Denied(OUTSIDE_AREA)
        return real

    def contained(self, path):
        real = os.path.realpath(path)
        if not sitepath.inside(self.root, real):
            raise Denied(OUTSIDE_TENANT)
        return real

    def walk_files(self, folder):
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
            # Ensure directory traversal stays within allowed areas
            if not self._is_allowed_area(real, 'dir'):
                continue
            rel = name if not prefix else prefix + "/" + name
            if os.path.isdir(real):
                self._walk(real, rel, found, seen)
            elif os.path.isfile(real):
                found.append((real, rel))

    def show(self, path):
        return sitepath.display(self.root, path)

    def read_text(self, real):
        # Ensure read operations are properly validated
        real = self.contained(real)
        if not os.path.lexists(real):
            raise SiteError("not found")
        if os.path.isdir(real):
            raise SiteError("not a file")
        return self.guard.read_text(real)

    def read_bytes(self, real):
        # Ensure read operations are properly validated
        real = self.contained(real)
        if not os.path.lexists(real):
            raise SiteError("not found")
        if os.path.isdir(real):
            raise SiteError("not a file")
        return self.guard.read_bytes(real)

    def variables(self):
        merged = {"tenant": self.name}
        merged.update(self.config.variables)
        merged.update(self.session_vars)
        return merged

    def _is_allowed_area(self, path, operation):
        """Check if path is in allowed area for given operation (read/write/dir)"""
        area_map = {
            'read': [self.src, self.out, self.cache_dir],
            'write': [self.out, self.exports, self.cache_dir],
            'dir': [self.src, self.out, self.cache_dir, self.exports]
        }
        for area in area_map.get(operation, []):
            if sitepath.inside(os.path.realpath(area), os.path.realpath(path)):
                return True
        return False


def open_tenant(workspace, name):
    if not NAME_RE.match(name) or name in (".", ".."):
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