# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Path helpers for mapping user supplied paths into a user's folder.

All paths typed by users are relative to the user's folder. A leading slash is
not special: "/docs/a.txt" means "docs/a.txt" inside the folder.
"""

import os

from errors import Denied


def clean_rel(rel):
    return rel.lstrip("/")


def join_user(user_root, rel):
    """Join a user supplied path onto the user's folder (text only)."""
    return os.path.join(user_root, clean_rel(rel))


def within_real(user_root, real):
    """True when an already resolved path is the folder or lies below it."""
    return real == user_root or real.startswith(user_root + os.sep)


def resolve_real(user_root, rel):
    """Resolve a user supplied path and require it to stay in the folder."""
    if ".." in rel or any(os.path.islink(os.path.join(user_root, p)) for p in rel.split("/")[:1]):
        raise Denied()
    real = os.path.realpath(join_user(user_root, rel))
    if not within_real(user_root, real):
        raise Denied()
    return real
