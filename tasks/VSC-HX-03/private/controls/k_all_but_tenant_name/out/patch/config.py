# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Parsers for a tenant's ``site.cfg`` and for page front matter.

site.cfg, one setting per line (blank lines and ``#`` comments ignored):

    var NAME = VALUE          a site variable for templates
    plugin NAME ARG...        register a built-in plugin (see plugins.py)

Front matter is an optional block at the very top of a page or layout:

    ---
    title: Hello
    layout: base.html
    ---
"""

import re

from errors import SiteError

VAR_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
FRONT_KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s?(.*)\Z")


class SiteConfig:
    def __init__(self, variables=None, plugins=None):
        self.variables = dict(variables or {})
        # list of (plugin name, [args]) in file order
        self.plugins = list(plugins or [])

    def fingerprint(self):
        """Text that changes whenever a setting that affects rendering changes."""
        parts = ["%s=%s" % item for item in sorted(self.variables.items())]
        parts += [" ".join([name] + args) for name, args in self.plugins]
        return "\n".join(parts)


def parse_site_cfg(text):
    variables = {}
    plugins = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        word, _, rest = line.partition(" ")
        if word == "var":
            name, eq, value = rest.partition("=")
            name = name.strip()
            if not eq or not VAR_NAME.match(name):
                raise SiteError("bad config line %d" % number)
            variables[name] = value.strip()
        elif word == "plugin":
            fields = rest.split()
            if not fields:
                raise SiteError("bad config line %d" % number)
            plugins.append((fields[0], fields[1:]))
        else:
            raise SiteError("bad config line %d" % number)
    return SiteConfig(variables, plugins)


def split_front_matter(text):
    """Return (metadata dict, body text). Text without front matter is all body."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return {}, text
    meta = {}
    for index in range(1, len(lines)):
        line = lines[index].rstrip("\r\n")
        if line == "---":
            return meta, "".join(lines[index + 1:])
        if not line.strip():
            continue
        match = FRONT_KEY.match(line)
        if match is None:
            raise SiteError("bad front matter")
        meta[match.group(1)] = match.group(2).strip()
    raise SiteError("bad front matter")
