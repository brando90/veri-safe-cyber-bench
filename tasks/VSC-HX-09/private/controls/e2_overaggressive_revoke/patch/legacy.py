# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version 0 helpers, kept for the offline migration tool.

The command interpreter does not use anything in this module.  Version 0
bundles had no checksum and no set line; version 0 patterns were shell
globs.  New code must use patterns.py and bundle.py.
"""
import fnmatch

V0_HEADER = "policyforge-bundle 0"


def match_v0(pattern, value):
    """Version 0 matching: shell-style globbing on the whole text."""
    return fnmatch.fnmatchcase(value, pattern)


def read_bundle_v0(lines):
    """Parse a version 0 bundle into (effect, action, resource, cond) tuples."""
    rules = []
    if not lines or lines[0].strip() != V0_HEADER:
        return rules
    for line in lines[1:]:
        parts = line.split(None, 3)
        if len(parts) < 3:
            continue
        cond = ""
        if len(parts) == 4:
            rest = parts[3]
            if rest.startswith("when "):
                cond = rest[5:].strip()
        rules.append((parts[0], parts[1], parts[2], cond))
    return rules


def convert_v0(lines):
    """Rewrite a version 0 bundle as version 1 body lines (no checksum)."""
    out = ["policyforge-bundle 1", "set migrated mode=standard parent=-"]
    for i, (effect, action, resource, cond) in enumerate(read_bundle_v0(lines), start=1):
        if resource.endswith("*") and not resource.endswith("/**"):
            resource = resource[:-1] + "**" if resource.endswith("/*") else resource
        line = "rule R%d %s %s %s" % (i, effect, action, resource)
        if cond:
            line += " when " + cond
        out.append(line)
    return out


def pct_v0(n, d):
    """Version 0 percentages (float formatting); superseded by numfmt.pct1."""
    if not d:
        return "0.0"
    return "%.1f" % (100.0 * n / d)


def precedence_v0(effects):
    """Version 0 precedence: the first matching rule decided."""
    for effect in effects:
        if effect in ("allow", "deny"):
            return effect
    return "deny"
