# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Log records and the parser for the log command."""
import hashlib

import names
import stamp
from errors import Rejected

SEPARATOR = " -- "


class Record:
    def __init__(self, rid, when, source, user, fields, message):
        self.id = rid
        self.when = when
        self.source = source
        self.user = user
        self.fields = fields
        self.message = message
        self.size = 0

    def fingerprint(self):
        parts = [stamp.fmt(self.when), self.source, self.user, self.message]
        parts.extend("%s=%s" % item for item in sorted(self.fields.items()))
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def domain_of(user):
    """The part of a user name after its last @, or '-' when there is none."""
    domain, at, local = user.partition("@")
    return domain if at and domain else "-"


def parse_size(fields):
    """The bytes field as a number; absent or empty counts as 0, None if malformed."""
    raw = fields.get("bytes", "0")
    if not (raw.isascii() and raw.isdigit()):
        return None
    return int(raw)


def parse_fields(tokens):
    fields = {}
    for token in tokens:
        name, sep, value = token.partition("=")
        if not sep or not name:
            raise Rejected("bad field %s" % (name or token))
        fields[names.fold(name)] = value
    return fields


def parse_log(rest, rid):
    head, sep, message = rest.partition(SEPARATOR)
    if not sep and head.endswith(" --"):
        head, message = head[:-3], ""
    tokens = head.split()
    if len(tokens) < 3:
        raise Rejected("missing fields")
    when = stamp.parse(tokens[0])
    if when is None:
        raise Rejected("bad timestamp")
    source = tokens[1].lower()
    if not all(c.isalnum() or c in "._-" for c in source):
        raise Rejected("bad source")
    fields = parse_fields(tokens[3:])
    size = parse_size(fields)
    if size is None:
        raise Rejected("bad bytes")
    record = Record(rid, when, source, tokens[2], fields, message.strip())
    record.size = size
    return record
