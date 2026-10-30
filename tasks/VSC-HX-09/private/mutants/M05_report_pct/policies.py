# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Policy sets and rules.

A policy set has a name, a mode (`standard` or `admin`), an optional parent
set and an ordered list of rules.  A set's rules apply to checks made
against the set and against every set that inherits from it.  Rule ids are
global (R1, R2, ...) and never reused.
"""
import re

import limits
import macros
import patterns
from errors import RuleError, SetError

EFFECTS = ("allow", "deny", "override")
MODES = ("standard", "admin")
_NAME_RE = re.compile(limits.NAME_PATTERN)


class Rule:
    def __init__(self, rid, set_name, effect, action, resource, cond_text, cond_ast):
        self.id = rid
        self.set_name = set_name
        self.effect = effect
        self.action = action
        self.resource = resource
        self.cond_text = cond_text
        self.cond_ast = cond_ast

    def label(self):
        return "R%d" % self.id

    def spec(self):
        text = "%s %s %s" % (self.effect, self.action, self.resource)
        if self.cond_text:
            text += " when " + self.cond_text
        return text


class PolicySet:
    def __init__(self, name, parent, mode):
        self.name = name
        self.parent = parent
        self.mode = mode
        self.rules = []


class RuleSpec:
    """A rule that has been validated but not yet stored."""

    def __init__(self, effect, action, resource, cond_text, cond_ast):
        self.effect = effect
        self.action = action
        self.resource = resource
        self.cond_text = cond_text
        self.cond_ast = cond_ast


class PolicyStore:
    def __init__(self):
        self.sets = {}
        self.next_id = 1

    # -- sets ----------------------------------------------------------------
    def create(self, name, parent=None, mode="standard"):
        if not _NAME_RE.fullmatch(name):
            raise SetError("bad set name %s" % name)
        if name in self.sets:
            raise SetError("set %s already exists" % name)
        if mode not in MODES:
            raise SetError("bad mode %s" % mode)
        if parent is not None:
            self.get(parent)
        pset = PolicySet(name, parent, mode)
        self.sets[name] = pset
        return pset

    def get(self, name):
        pset = self.sets.get(name)
        if pset is None:
            raise SetError("unknown set %s" % name)
        return pset

    def chain(self, name):
        """The set and its ancestors, nearest first."""
        out = []
        cur = self.get(name)
        while cur is not None:
            out.append(cur)
            cur = self.sets[cur.parent] if cur.parent else None
        return out

    def reparent(self, name, parent):
        pset = self.get(name)
        if parent is not None:
            if any(s.name == name for s in self.chain(parent)):
                raise SetError("%s cannot inherit from %s (cycle)" % (name, parent))
        pset.parent = parent

    def set_mode(self, name, mode):
        pset = self.get(name)
        if mode not in MODES:
            raise SetError("bad mode %s" % mode)
        if mode == "standard" and any(r.effect == "override" for r in pset.rules):
            raise SetError("%s still holds override rules" % name)
        pset.mode = mode

    def children(self, name):
        return sorted(s.name for s in self.sets.values() if s.parent == name)

    # -- rules -----------------------------------------------------------------
    def validate_rule(self, mode, effect, action, resource, cond_text, table):
        """Check one rule for a set of MODE; return a RuleSpec."""
        if effect not in EFFECTS:
            raise RuleError("bad effect %s" % effect)
        if effect == "override" and mode != "admin":
            raise RuleError("override rules need an admin set")
        patterns.check_action(action)
        patterns.check_resource(resource)
        cond_ast = None
        if cond_text:
            cond_ast = macros.compile_condition(table, cond_text)
        return RuleSpec(effect, action, resource, cond_text, cond_ast)

    def add(self, set_name, specs):
        """Store validated RuleSpecs in SET_NAME; return the new rules."""
        pset = self.get(set_name)
        added = []
        for spec in specs:
            rule = Rule(self.next_id, pset.name, spec.effect, spec.action, spec.resource,
                        spec.cond_text, spec.cond_ast)
            self.next_id += 1
            pset.rules.append(rule)
            added.append(rule)
        return added

    def add_rule(self, set_name, effect, action, resource, cond_text, table):
        pset = self.get(set_name)
        spec = self.validate_rule(pset.mode, effect, action, resource, cond_text, table)
        return self.add(set_name, [spec])[0]

    def find_rule(self, rid):
        for pset in self.sets.values():
            for rule in pset.rules:
                if rule.id == rid:
                    return rule
        raise RuleError("unknown rule R%d" % rid)

    def remove_rule(self, rid):
        rule = self.find_rule(rid)
        pset = self.sets[rule.set_name]
        pset.rules = [r for r in pset.rules if r.id != rid]
        return rule

    def all_rules(self):
        for name in sorted(self.sets):
            for rule in self.sets[name].rules:
                yield rule


def parse_rule_id(text):
    if not re.fullmatch(r"R[1-9][0-9]{0,8}", text):
        raise RuleError("bad rule id %s" % text)
    return int(text[1:])
