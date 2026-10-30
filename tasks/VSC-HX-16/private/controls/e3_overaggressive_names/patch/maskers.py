# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Value maskers: partial mask, pseudonym and the fixed redaction marker."""
import hashlib

MASK_CHAR = "*"
REDACTED = "[redacted]"
_MEMO = {}


def visible(length):
    """Length of the visible tail of a partial mask."""
    return length // 4 if length >= 8 else 0


def partial(value):
    keep = visible(len(value))
    return MASK_CHAR * (len(value) - keep) + value[len(value) - keep:]


def pseudo(value, salt, _memo=_MEMO):
    key = (salt, value)
    if key not in _memo:
        digest = hashlib.sha256((salt + "\0" + value).encode("utf-8")).hexdigest()
        _memo[key] = "p-" + digest[:8]
    return _memo[key]
