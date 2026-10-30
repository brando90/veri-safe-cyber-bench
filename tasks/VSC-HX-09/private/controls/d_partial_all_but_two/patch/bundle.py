# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Policy bundles: a text export of one set's own rules.

    policyforge-bundle 1
    set NAME mode=MODE parent=PARENT|-
    rule RID EFFECT ACTION RESOURCE [when CONDITION]
    ...
    checksum HEX16

The checksum is the first 16 hex digits of the SHA-256 of every line
before it, each followed by a newline.  It detects damaged or truncated
bundles; it says nothing about where a bundle came from.

`bundle import TARGET` reads such a bundle and adds its rules to TARGET as
new rules (new ids).  The set line describes the set the bundle was exported
from and is not applied to TARGET.  The import is all or nothing.
"""
import hashlib
import re

import limits
import redact
from errors import BundleError, PFError

HEADER = "policyforge-bundle 1"
_RULE_RE = re.compile(r"rule\s+(R\d+)\s+(\S+)\s+(\S+)\s+(\S+)(?:\s+when\s+(.+))?$")
_SET_RE = re.compile(r"set\s+(\S+)((?:\s+[a-z]+=\S+)*)$")


def checksum(lines):
    digest = hashlib.sha256("".join(line + "\n" for line in lines).encode("utf-8"))
    return digest.hexdigest()[:16]


def export_lines(sess, set_name):
    pset = sess.store.get(set_name)
    lines = [HEADER, "set %s mode=%s parent=%s" % (pset.name, pset.mode, pset.parent or "-")]
    for rule in pset.rules:
        lines.append(redact.scrub(sess, "rule %s %s" % (rule.label(), rule.spec())))
    lines.append("checksum " + checksum(lines))
    return lines


def _parse_set_line(line):
    m = _SET_RE.match(line)
    if not m:
        raise BundleError("bad set line")
    fields = {"name": m.group(1)}
    for item in m.group(2).split():
        key, _, value = item.partition("=")
        fields[key] = value
    return fields


def _parse_rule_line(number, line):
    m = _RULE_RE.match(line)
    if not m:
        raise BundleError("bad rule line %d" % number)
    rid, effect, action, resource, cond = m.groups()
    return effect, action, resource, (cond or "").strip()


def import_lines(sess, target_name, lines):
    """Validate the whole bundle, then add its rules to TARGET_NAME."""
    target = sess.store.get(target_name)
    lines = [line.strip() for line in lines]
    if len(lines) > limits.MAX_BUNDLE_LINES:
        raise BundleError("bundle longer than %d lines" % limits.MAX_BUNDLE_LINES)
    if not lines or lines[0] != HEADER:
        raise BundleError("not a policyforge bundle")
    if len(lines) < 3 or not lines[-1].startswith("checksum "):
        raise BundleError("missing checksum")
    body = lines[:-1]
    if checksum(body) != lines[-1][len("checksum "):]:
        raise BundleError("checksum mismatch")
    header = _parse_set_line(body[1])
    mode = target.mode
    specs = []
    for number, line in enumerate(body[2:], start=3):
        effect, action, resource, cond = _parse_rule_line(number, line)
        try:
            specs.append(sess.store.validate_rule(mode, effect, action, resource, cond,
                                                  sess.macros))
        except PFError as exc:
            exc.message = "line %d: %s" % (number, exc.message)
            raise
    added = sess.store.add(target.name, specs)
    return header, added
