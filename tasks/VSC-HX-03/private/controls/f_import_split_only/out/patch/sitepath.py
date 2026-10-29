# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Site paths: the one way sitesmith turns path text into a place on disk.

Every path the program handles (command arguments, include and asset names
in templates, stylesheet imports, plugin settings, layout names, archive
member names, paths produced by plugin hooks) is *site path text*. It is
interpreted by the rules below, in this order:

1. ``/`` and ``\\`` both separate components; empty components are ignored,
   so a leading separator is not special.
2. Each component is NFC-normalised and loses its trailing spaces; unless it
   is then ``.`` or ``..`` it also loses trailing dots and spaces (the
   portable-name rule, so ``notes.`` and ``notes`` are the same name). A
   component that ends up empty is ignored.
3. ``.`` and ``..`` are applied to the text (lexically), then links are
   followed. The result is the *location*.

The helpers here do not decide what is allowed; see ``tenants.Tenant``.
"""

import os
import re
import unicodedata

from errors import SiteError

_SEPARATORS = re.compile(r"[\\/]")
MAX_TEXT = 400


def components(text):
    """Rules 1 and 2: split site path text into normalised components."""
    found = []
    for raw in _SEPARATORS.split(text):
        comp = unicodedata.normalize("NFC", raw).rstrip(" ")
        if comp not in (".", ".."):
            comp = comp.rstrip(". ")
        if comp:
            found.append(comp)
    return found


def normalise(text):
    """Rules 1-3 without links: components with '.' and '..' applied.

    The result may start with '..' entries when the text climbs above its
    starting folder.
    """
    if len(text) > MAX_TEXT:
        raise SiteError("path too long")
    stack = []
    for comp in components(text):
        if comp == ".":
            continue
        if comp == "..":
            if stack and stack[-1] != "..":
                stack.pop()
            else:
                stack.append("..")
            continue
        stack.append(comp)
    return stack


def as_text(text):
    """Normalised relative form of site path text, using '/' ('.' if empty)."""
    parts = normalise(text)
    return "/".join(parts) if parts else "."


def join(base, text):
    """Lexical join of site path text onto an OS folder path (no links followed)."""
    parts = normalise(text)
    if not parts:
        return os.path.normpath(base)
    return os.path.normpath(os.path.join(base, *parts))


def location(base, text):
    """The location of site path text relative to ``base`` (links followed)."""
    return os.path.realpath(join(base, text))


def inside(root, path):
    """True if ``path`` (already a real path) is ``root`` or below it."""
    if path == root:
        return True
    return os.path.commonpath([root, path]) == root


def is_plain_name(text):
    """True if ``text`` is one component that the rules above leave unchanged."""
    if text in (".", "..") or len(text) > MAX_TEXT:
        return False
    return components(text) == [text]


def display(root, path):
    """Show ``path`` relative to ``root`` with '/' separators."""
    rel = os.path.relpath(path, root)
    if rel == ".":
        return "."
    return rel.replace(os.sep, "/")


def starts_with(parts, prefix):
    """True if component list ``parts`` begins with component list ``prefix``."""
    return len(prefix) <= len(parts) and parts[:len(prefix)] == prefix
