# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version numbers MAJOR.MINOR.PATCH[-PRE] and their order."""
import re

_NUM = r"(0|[1-9]\d{0,5})"
_PRE = r"[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*"
_FULL_RE = re.compile(r"%s\.%s\.%s(?:-(%s))?" % (_NUM, _NUM, _NUM, _PRE))
_PARTIAL_RE = re.compile(r"%s(?:\.%s(?:\.%s(?:-(%s))?)?)?" % (_NUM, _NUM, _NUM, _PRE))


class Version:
    __slots__ = ("major", "minor", "patch", "pre", "text")

    def __init__(self, major, minor, patch, pre=()):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.pre = tuple(pre)
        self.text = "%d.%d.%d" % (major, minor, patch)
        if self.pre:
            self.text += "-" + ".".join(self.pre)

    @property
    def core(self):
        return (self.major, self.minor, self.patch)

    def __repr__(self):
        return "Version(%s)" % self.text


def _pre_part(ident):
    if ident.isdigit():
        return (0, int(ident), "")
    return (1, 0, ident)


def key(v):
    """Sort key: numeric parts, then a release after its pre-releases, then
    pre-release identifiers (numeric ones numerically, before text ones)."""
    return (v.major, v.minor, v.patch, 0 if v.pre else 1, tuple(_pre_part(p) for p in v.pre))


def parse(text):
    """The Version written as TEXT, or None."""
    m = _FULL_RE.fullmatch(text or "")
    if m is None:
        return None
    pre = m.group(4).split(".") if m.group(4) else ()
    for ident in pre:
        if ident.isdigit() and len(ident) > 1 and ident[0] == "0":
            return None
    return Version(int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)


def parse_partial(text):
    """(Version, number of parts given) for ``1``, ``1.2``, ``1.2.3[-pre]``."""
    m = _PARTIAL_RE.fullmatch(text or "")
    if m is None:
        return None, 0
    given = 1 + (m.group(2) is not None) + (m.group(3) is not None)
    if m.group(4):
        v = parse(text)
        return v, (3 if v is not None else 0)
    nums = [int(g) if g is not None else 0 for g in m.group(1, 2, 3)]
    return Version(*nums), given


def sort_versions(versions):
    return sorted(versions, key=key)
