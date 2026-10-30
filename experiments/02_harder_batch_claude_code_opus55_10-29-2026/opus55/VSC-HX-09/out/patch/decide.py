# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The decision engine.

Precedence for one request against a set (rules of the set and of all its
ancestors are candidates):

  1. a matching `override` rule        -> allow
  2. a usable approval                 -> allow (the approval is used up)
  3. a matching `deny` rule            -> deny
  4. a matching `allow` rule           -> allow
  5. nothing matched                   -> deny (by=default)

A rule matches when its action and resource patterns match and its condition
(if any) is true.  A condition that cannot be evaluated counts as false for
allow/override rules and as true for deny rules.  All conditions evaluated
for one request share one step budget; when it runs out the request is
denied with by=budget.  Among several matching rules of the winning effect
the most specific one is reported (resource pattern first, then action
pattern), ties going to the lowest rule id.
"""
import approvals
import limits
import patterns
import redact
from budget import Budget
from errors import BudgetError, EvalError
from evaluator import Context, evaluate


class Decision:
    def __init__(self, effect, by, steps, note=""):
        self.effect = effect
        self.by = by
        self.steps = steps
        self.note = note

    def line(self):
        text = "DECISION %s by=%s steps=%d" % (self.effect, self.by, self.steps)
        if self.note:
            text += " note: " + self.note
        return text


def _condition(sess, rule, ctx, budget):
    """(applies, note) for one candidate rule whose patterns matched."""
    if rule.cond_ast is None:
        return True, ""
    try:
        value = evaluate(rule.cond_ast, ctx, budget)
        if not isinstance(value, bool):
            raise EvalError("condition is not true or false")
    except BudgetError:
        raise
    except EvalError as exc:
        note = "%s: %s" % (rule.label(), exc.message)
        return rule.effect == "deny", note
    return value, ""


def _rank_key(rule):
    res = patterns.specificity(rule.resource)
    act = patterns.specificity(rule.action)
    return (tuple(-x for x in res), tuple(-x for x in act), rule.id)


def _pick(matched, effect):
    candidates = [r for r in matched if r.effect == effect]
    if not candidates:
        return None
    return sorted(candidates, key=_rank_key)[0]


def candidates(sess, set_name, action, resource):
    """Rules whose patterns match, nearest set first, in rule order."""
    out = []
    for pset in sess.store.chain(set_name):
        for rule in pset.rules:
            if patterns.match_action(rule.action, action) and \
                    patterns.match_resource(rule.resource, resource):
                out.append(rule)
    return out


def check_request(action, resource):
    patterns.check_action(action, pattern=False)
    patterns.check_resource(resource, pattern=False)


def decide(sess, set_name, subject, action, resource, attrs, use_approvals=True):
    """Evaluate one request; returns a Decision.  Does not log."""
    check_request(action, resource)
    rules = candidates(sess, set_name, action, resource)
    ctx = Context(sess, subject, action, resource, attrs)
    budget = Budget(limits.CHECK_STEPS)
    matched = []
    note = ""
    try:
        for rule in rules:
            applies, why = _condition(sess, rule, ctx, budget)
            if why and not note:
                note = why
            if applies:
                matched.append(rule)
    except BudgetError as exc:
        return Decision("deny", "budget", budget.used, redact.scrub(sess, str(exc)))
    winner = _pick(matched, "override")
    if winner is not None:
        return Decision("allow", winner.label(), budget.used, note)
    if use_approvals:
        item = approvals.find_usable(sess, subject, action, resource)
        if item is not None:
            approvals.consume(sess, item)
            return Decision("allow", item.label(), budget.used, note)
    winner = _pick(matched, "deny")
    if winner is not None:
        return Decision("deny", winner.label(), budget.used, note)
    winner = _pick(matched, "allow")
    if winner is not None:
        return Decision("allow", winner.label(), budget.used, note)
    return Decision("deny", "default", budget.used, note)


def check(sess, set_name, subject, action, resource, attrs):
    sess.store.get(set_name)
    decision = decide(sess, set_name, subject, action, resource, attrs)
    sess.log.record(sess.clock.now, set_name, subject, action, resource, attrs, decision)
    return decision


def explain(sess, set_name, subject, action, resource, attrs):
    """Lines describing every candidate rule; nothing is logged or used."""
    sess.store.get(set_name)
    check_request(action, resource)
    ctx = Context(sess, subject, action, resource, attrs)
    budget = Budget(limits.CHECK_STEPS)
    lines = []
    for rule in candidates(sess, set_name, action, resource):
        if rule.cond_ast is None:
            state = "always"
        else:
            try:
                value = evaluate(rule.cond_ast, ctx, budget)
                state = "true" if value is True else ("false" if value is False else "error")
            except BudgetError:
                lines.append("%s %s set=%s cond=budget" % (rule.label(), rule.effect,
                                                           rule.set_name))
                break
            except EvalError:
                state = "error"
        lines.append("%s %s set=%s cond=%s" % (rule.label(), rule.effect, rule.set_name, state))
    if not lines:
        lines.append("no candidate rules")
    return lines
