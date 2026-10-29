# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""szip archives: EXPORT, TOC and IMPORT.

An szip archive is a simple byte format, readable in a text editor:

    SZIP1
    F <size> <member name>
    <size bytes of content>
    (one newline)
    ... more F records ...
    END <number of members>

EXPORT packs every file below out/ (links followed, each real folder once)
into exports/NAME.szip, members named by their path below out/, sorted.
IMPORT unpacks an archive into src/themes/THEME/; member names are site
path text relative to that folder. TOC lists the members of an export.
"""

import os
import re

from errors import OUTSIDE_AREA, Denied

import sitepath
from errors import SiteError

MAGIC = b"SZIP1\n"
RECORD = re.compile(rb"F (\d{1,9}) (.+)\Z")
END = re.compile(rb"END (\d{1,9})\Z")


class Catalogued:
    """What EXPORT remembers about an archive it wrote, so TOC can skip parsing."""

    def __init__(self, path, size, members):
        self.path = path
        self.size = size
        self.members = members


_catalog = {}


def pack(members):
    out = [MAGIC]
    for name, data in members:
        out.append(b"F %d %s\n" % (len(data), name.encode("utf-8")))
        out.append(data)
        out.append(b"\n")
    out.append(b"END %d\n" % len(members))
    return b"".join(out)


def _line(data, pos):
    end = data.find(b"\n", pos)
    if end < 0:
        raise SiteError("bad archive")
    return data[pos:end], end + 1


def unpack(data):
    """List of (member name, content bytes); raises 'bad archive' if malformed."""
    if not data.startswith(MAGIC):
        raise SiteError("bad archive")
    pos = len(MAGIC)
    members = []
    while True:
        line, pos = _line(data, pos)
        end = END.match(line)
        if end is not None:
            if int(end.group(1)) != len(members) or pos != len(data):
                raise SiteError("bad archive")
            return members
        record = RECORD.match(line)
        if record is None:
            raise SiteError("bad archive")
        size = int(record.group(1))
        try:
            name = record.group(2).decode("utf-8")
        except UnicodeDecodeError:
            raise SiteError("bad archive") from None
        content = data[pos:pos + size]
        if len(content) != size or data[pos + size:pos + size + 1] != b"\n":
            raise SiteError("bad archive")
        members.append((name, content))
        pos += size + 1


def export(tenant, name):
    """EXPORT NAME -> (member count, archive size)."""
    if not sitepath.is_plain_name(name):
        raise SiteError("bad archive name")
    dest = tenant.locate_for_write(tenant.exports, tenant.exports, name + ".szip")
    members = []
    if os.path.isdir(tenant.out):
        for real, rel in tenant.walk_files(tenant.out):
            members.append((rel, tenant.read_bytes(real)))
    data = pack(members)
    tenant.guard.write_bytes(dest, data)
    listing = [(rel, len(content)) for rel, content in members]
    _catalog[(tenant.root, name)] = Catalogued(dest, len(data), listing)
    return len(members), len(data)


def toc(tenant, name):
    """TOC NAME -> list of (member name, size)."""
    if not sitepath.is_plain_name(name):
        raise SiteError("bad archive name")
    known = _catalog.get((tenant.root, name))
    if known is not None and os.path.isfile(known.path) \
            and os.path.getsize(known.path) == known.size:
        return list(known.members)
    path = tenant.locate(tenant.exports, name + ".szip")
    if not os.path.isfile(path):
        raise SiteError("no such archive")
    return [(member, len(content)) for member, content in unpack(tenant.read_bytes(path))]


def import_archive(tenant, text, theme):
    """IMPORT PATH THEME -> number of files written below src/themes/THEME."""
    if not sitepath.is_plain_name(theme):
        raise SiteError("bad theme name")
    source = tenant.locate(tenant.root, text)
    if not os.path.isfile(source):
        raise SiteError("no such archive")
    members = unpack(tenant.read_bytes(source))
    theme_dir = tenant.folder("src", "themes", theme)
    plan = []
    for member, content in members:
        if not sitepath.normalise(member) or sitepath.normalise(member)[0] == "..":
            raise Denied(OUTSIDE_AREA)
        dest = sitepath.join(theme_dir, member)
        plan.append((dest, content))
    for dest, content in plan:
        tenant.guard.write_bytes(dest, content)
    return len(plan)
