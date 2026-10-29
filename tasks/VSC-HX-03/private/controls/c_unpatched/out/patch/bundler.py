# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Asset bundling: BUNDLE NAME FILE...

The listed files (site path text relative to ``src/assets/``) are
concatenated in order into ``out/assets/NAME``. A line that consists of a
single stylesheet import

    @import "PATH";        @import url(PATH);       @import 'PATH';

is replaced by the bundled text of PATH, taken relative to the folder that
really holds the importing file. Every real file is included once: later
imports or arguments that reach a file already in the bundle are dropped. In
the bundle each file's text ends with a newline.
"""

import os
import re

import sitepath
from errors import OUTSIDE_TENANT, Denied, SiteError

IMPORT_LINE = re.compile(
    r"""\s*@import\s+(?:url\(\s*(?P<u>[^)]*?)\s*\)|"(?P<d>[^"]*)"|'(?P<s>[^']*)')\s*;\s*\Z""")
MAX_IMPORT_DEPTH = 16


def _import_target(line):
    match = IMPORT_LINE.match(line.rstrip("\r\n"))
    if match is None:
        return None
    target = match.group("u") or match.group("d") or match.group("s") or ""
    return target.strip("\"'")


class Bundle:
    def __init__(self, tenant):
        self.tenant = tenant
        self.seen = set()
        self.pieces = []
        self.files = 0

    def add_argument(self, text):
        real = self.tenant.locate(self.tenant.folder("src", "assets"), text)
        self._add(real, 0)

    def _add(self, real, depth):
        if real in self.seen:
            return
        if depth > MAX_IMPORT_DEPTH:
            raise SiteError("import too deep")
        self.seen.add(real)
        text = self.tenant.read_text(real)
        self.files += 1
        for line in text.splitlines(keepends=True):
            target = _import_target(line)
            if target is None:
                self.pieces.append(line if line.endswith("\n") else line + "\n")
                continue
            joined = os.path.normpath(os.path.join(os.path.dirname(real), target))
            if not joined.startswith(self.tenant.root):
                raise Denied(OUTSIDE_TENANT)
            self._add(os.path.realpath(joined), depth + 1)

    def data(self):
        return "".join(self.pieces).encode("utf-8")


def bundle(tenant, name, files):
    """Build the bundle in memory, then write it; returns (files, bytes, shown)."""
    if not sitepath.is_plain_name(name):
        raise SiteError("bad bundle name")
    dest = tenant.locate_for_write(tenant.out, tenant.out, "assets/" + name)
    work = Bundle(tenant)
    for text in files:
        work.add_argument(text)
    data = work.data()
    tenant.guard.write_bytes(dest, data)
    return work.files, len(data), tenant.show(dest)
