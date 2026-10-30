# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""`lint SET`: static remarks about the rules that apply to a set.

Remarks (one line each, rule order, nearest set first):
  LINT Rn duplicates Rm            same effect, patterns and condition
  LINT Rn is shadowed by Rm        an allow rule whose patterns are covered
                                   by an unconditional deny rule (and no
                                   override could decide first)
  LINT Rn refers to unknown secret NAME
  LINT Rn never matches: ...       patterns that cannot select anything
Lint never changes anything and evaluates no condition.
"""
import parser


def covers_resource(general, specific):
    """True if every resource selected by SPECIFIC is selected by GENERAL."""
    gen = general[1:].split("/")
    spe = specific[1:].split("/")
    if gen[-1] == "**":
        head = gen[:-1]
        if spe[-1] == "**":
            spe_head = spe[:-1]
            if len(spe_head) < len(head):
                return False
        elif len(spe) < len(head):
            return False
        return all(g == "*" and s != "**" or g == s for g, s in zip(head, spe))
    if spe[-1] == "**" or len(gen) != len(spe):
        return False
    return all((g == "*" and s != "**") or g == s for g, s in zip(gen, spe))


def covers_action(general, specific):
    if general == "*":
        return True
    if specific == "*":
        return False
    gns, _, gverb = general.partition(":")
    sns, _, sverb = specific.partition(":")
    return (gns == "*" or gns == sns) and (gverb == "*" or gverb == sverb)


def _names(node, prefix, out):
    kind = node[0]
    if kind == "name" and node[1].startswith(prefix):
        out.append(node[1][len(prefix):])
    elif kind == "list":
        for item in node[1]:
            _names(item, prefix, out)
    elif kind == "call":
        for item in node[2]:
            _names(item, prefix, out)
    elif kind == "not":
        _names(node[1], prefix, out)
    elif kind in ("and", "or", "in"):
        _names(node[1], prefix, out)
        _names(node[2], prefix, out)
    elif kind == "cmp":
        _names(node[2], prefix, out)
        _names(node[3], prefix, out)
    return out


def _secret_refs(sess, rule):
    if rule.cond_ast is None:
        return []
    refs = _names(rule.cond_ast, "secret.", [])
    for name in parser.macro_refs(rule.cond_ast):
        refs.extend(_names(sess.macros.get(name).ast, "secret.", []))
    out = []
    for ref in refs:
        if ref not in out:
            out.append(ref)
    return out


def _never_matches(rule):
    segs = rule.resource[1:].split("/")
    if len(segs) > 32:
        return "resource pattern deeper than 32 segments"
    return None


def lint_lines(sess, set_name):
    rules = []
    for pset in sess.store.chain(set_name):
        rules.extend(pset.rules)
    lines = []
    overrides = [r for r in rules if r.effect == "override"]
    for i, rule in enumerate(rules):
        for other in rules[:i]:
            if (other.effect, other.action, other.resource, other.cond_text) == \
                    (rule.effect, rule.action, rule.resource, rule.cond_text):
                lines.append("LINT %s duplicates %s" % (rule.label(), other.label()))
                break
        if rule.effect == "allow":
            for other in rules:
                if other.effect != "deny" or other.cond_ast is not None:
                    continue
                if covers_resource(other.resource, rule.resource) and \
                        covers_action(other.action, rule.action):
                    if not overrides:
                        lines.append("LINT %s is shadowed by %s" % (rule.label(), other.label()))
                        break
        for ref in _secret_refs(sess, rule):
            if ref not in sess.secrets:
                lines.append("LINT %s refers to unknown secret %s" % (rule.label(), ref))
        why = _never_matches(rule)
        if why:
            lines.append("LINT %s never matches: %s" % (rule.label(), why))
    if not lines:
        lines.append("LINT ok")
    return lines
