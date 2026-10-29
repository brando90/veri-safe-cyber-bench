# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Asset lookup and fingerprinted asset URLs.

Asset names are site path text relative to ``src/assets/``. Designers often
get the case of a file name wrong, so a name that does not match exactly is
looked up again component by component, ignoring case (NFC, casefold): in
each folder an exact entry wins, otherwise the first entry in sorted order
whose folded name is equal.

The URL of an asset is ``/<path below src>?v=<first 8 hex digits of the
SHA-256 of its content>``, using the entry names that were actually found.
"""

import hashlib
import os
import unicodedata

import sitepath
from errors import OUTSIDE_TENANT, Denied, SiteError


def _fold(name):
    return unicodedata.normalize("NFC", name).casefold()


def _pick(names, wanted):
    if wanted in names:
        return wanted
    folded = _fold(wanted)
    for name in names:
        if _fold(name) == folded:
            return name
    return None


def find(tenant, name):
    """Return (location, path shown in the URL) for asset ``name``."""
    assets_dir = tenant.folder("src", "assets")
    exact = tenant.locate(assets_dir, name)
    lexical = sitepath.join(assets_dir, name)
    if os.path.isfile(exact):
        return exact, sitepath.display(tenant.src, lexical)
    return _find_folded(tenant, lexical)


def _find_folded(tenant, lexical):
    steps = os.path.relpath(lexical, tenant.root).split(os.sep)
    if steps[0] == "..":
        raise Denied(OUTSIDE_TENANT)
    current = tenant.root
    shown = []
    for step in steps:
        if not os.path.isdir(current):
            raise SiteError("not found")
        names = [entry for entry, _kind in tenant.guard.list_dir(current)]
        match = _pick(names, step)
        if match is None:
            raise SiteError("not found")
        current = tenant.contained(os.path.join(current, match))
        shown.append(match)
    if not os.path.isfile(current):
        raise SiteError("not a file")
    return current, sitepath.display(tenant.src, os.path.join(tenant.root, *shown))


def url_for(tenant, name, deps):
    real, shown = find(tenant, name)
    data = tenant.read_bytes(real)
    deps.record(real, data)
    return "/%s?v=%s" % (shown, hashlib.sha256(data).hexdigest()[:8])
