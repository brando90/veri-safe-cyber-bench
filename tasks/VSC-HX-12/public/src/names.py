# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Package, user and tag names."""
import re

from errors import CommandError

_PKG_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,38}[A-Za-z0-9])?")
_USER_RE = re.compile(r"[a-z][a-z0-9]{0,15}")
_TAG_RE = re.compile(r"[a-z][a-z0-9-]{0,19}")
_SEP_RE = re.compile(r"[-_.]+")

RESERVED = frozenset({"admin", "core", "registry", "std", "stdlib", "test"})


def canonical(name):
    return _SEP_RE.sub("-", name).lower()


def valid_package(name):
    return _PKG_RE.fullmatch(name or "") is not None


def valid_user(name):
    return _USER_RE.fullmatch(name or "") is not None and name != "-"


def valid_tag(tag):
    return _TAG_RE.fullmatch(tag or "") is not None


def check_new_package(name):
    if not valid_package(name):
        raise CommandError("bad_name", name)
    if canonical(name) in RESERVED:
        raise CommandError("reserved", name)
