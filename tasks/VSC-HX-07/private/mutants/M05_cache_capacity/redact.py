# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Keeping secrets out of everything quotagate prints or records.

Two kinds of secret exist (README.md, "Secrets"):

* the secret part of a credential ``TENANT.KEYID.SECRET``; wherever a
  credential is shown it appears as ``TENANT.KEYID.***``, and text that
  cannot be parsed as a credential is shown as ``<malformed>``;
* configuration values whose name ends in ``.secret`` or ``.token``; they are
  shown as ``***`` (an empty value is shown empty).

``scrub`` is the last line of defence: the output layer and the audit log run
every line through it, so credential-shaped text that reaches them by any
route is masked.
"""
import re

TENANT_PATTERN = r"[a-z][a-z0-9-]{0,15}"
KEYID_PATTERN = r"[a-z0-9][a-z0-9_-]{0,15}"

_TENANT_RE = re.compile(TENANT_PATTERN + r"\Z")
_KEYID_RE = re.compile(KEYID_PATTERN + r"\Z")

# TENANT.KEYID.SECRET anywhere in a line; the secret part is masked.  The
# secret alphabet is the one keys.py accepts (letters, digits, '_' and '-').
_CREDENTIAL_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(%s)\.(%s)\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])"
    % (TENANT_PATTERN, KEYID_PATTERN))

SENSITIVE_SUFFIXES = (".secret", ".token")
MASK = "***"
MALFORMED = "<malformed>"


def split_credential(cred):
    """(tenant, keyid, secret) or None when CRED is not credential-shaped."""
    parts = cred.split(".", 2)
    if len(parts) != 3:
        return None
    tenant, keyid, secret = parts
    if not _TENANT_RE.match(tenant) or not _KEYID_RE.match(keyid) or not secret:
        return None
    return tenant, keyid, secret


def mask_credential(cred):
    parts = split_credential(cred)
    if parts is None:
        return MALFORMED
    return "%s.%s.%s" % (parts[0], parts[1], MASK)


def scrub(text):
    """Mask the secret part of every credential-shaped substring of TEXT."""
    return _CREDENTIAL_RE.sub(r"\1.\2." + MASK, text)


def is_sensitive(name):
    return name.endswith(SENSITIVE_SUFFIXES)


def show_value(name, value):
    """How a configuration value is displayed anywhere outside the config store."""
    if value == "":
        return ""
    if is_sensitive(name):
        return MASK
    return value
