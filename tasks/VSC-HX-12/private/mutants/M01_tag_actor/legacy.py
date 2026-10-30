# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version 1 manifest reader, kept for the old import tool.  Not used by
the command loop."""
import names
import semver


class ManifestV1:
    def __init__(self):
        self.name = None
        self.version = None
        self.deps = []
        self.extra = {}


def read_manifest_v1(text):
    """Parse ``key: value`` lines; ``dep: NAME SPEC`` may repeat."""
    m = ManifestV1()
    problems = []
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            problems.append("line %d: no colon" % no)
            continue
        key = key.strip().lower()
        value = value.strip()
        if key == "name":
            if not names.valid_package(value):
                problems.append("line %d: bad name" % no)
            m.name = value
        elif key == "version":
            if semver.parse(value) is None:
                problems.append("line %d: bad version" % no)
            m.version = value
        elif key == "dep":
            parts = value.split(None, 1)
            if len(parts) != 2:
                problems.append("line %d: bad dep" % no)
                continue
            m.deps.append((parts[0], parts[1]))
        else:
            m.extra[key] = value
    if m.name is None:
        problems.append("missing name")
    if m.version is None:
        problems.append("missing version")
    return m, problems


def manifest_v1_to_options(m):
    """Options for the publish command equivalent to a v1 manifest."""
    opts = {}
    if m.deps:
        opts["deps"] = ";".join("%s@%s" % (n, s) for n, s in m.deps)
    if "size" in m.extra:
        opts["size"] = m.extra["size"]
    return opts
