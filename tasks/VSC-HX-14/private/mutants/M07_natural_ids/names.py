# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Event ids and the natural order used when listings tie."""
import re

from errors import CommandError

ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9._-]{0,31}")
CHUNK_RE = re.compile(r"[0-9]+|[^0-9]+")


def check_id(text):
    if ID_RE.fullmatch(text) is None:
        raise CommandError("bad_id", text)
    return text


def natural_key(text):
    key = []
    for chunk in CHUNK_RE.findall(text)[:2]:
        if chunk[0] in "0123456789":
            key.append((1, int(chunk), len(chunk)))
        else:
            key.append((0, 0, chunk))
    return key
