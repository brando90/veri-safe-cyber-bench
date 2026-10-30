# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Command interpreter: one handler per command word.

Handlers validate all arguments before they change anything, and they
build their whole output with sess.emit(); main.py drops that output again
if the command fails.
"""
import re

import approvals
import bundle
import clock
import decide
import evaluator
import helptext
import limits
import lint
import macros
import patterns
import policies
import redact
import render
import stats
import template
import whatif
from budget import Budget
from errors import ApprovalError, LogError, SecretError, TemplateError, UsageError

_NAME_RE = re.compile(limits.NAME_PATTERN)
_SUBJECT_RE = re.compile(r"[A-Za-z0-9._@-]{1,64}")


# ---------------------------------------------------------------- helpers
def _rest(line, n):
    """The text after the first N blank-separated tokens of LINE."""
    text = line.strip()
    for _ in range(n):
        parts = text.split(None, 1)
        text = parts[1] if len(parts) > 1 else ""
    return text.strip()


def _need(toks, low, high, usage):
    if not low <= len(toks) <= high:
        raise UsageError("usage: " + usage)


def _name(text, what):
    if not _NAME_RE.fullmatch(text):
        raise UsageError("bad %s %s" % (what, text))
    return text


def _subject(text):
    if not _SUBJECT_RE.fullmatch(text):
        raise UsageError("bad subject %s" % text)
    return text


def _attrs(tokens):
    out = {}
    for tok in tokens:
        key, sep, value = tok.partition("=")
        if not sep or not value:
            raise UsageError("bad attribute %s" % tok)
        _name(key, "attribute name")
        if key in out:
            raise UsageError("attribute %s given twice" % key)
        out[key] = value
    return out


def _options(tokens, allowed):
    out = {}
    for tok in tokens:
        key, sep, value = tok.partition("=")
        if not sep or key not in allowed or not value:
            raise UsageError("bad option %s" % tok)
        out[key] = value
    return out


# ---------------------------------------------------------------- clock
def cmd_clock(sess, line, toks, more):
    _need(toks, 2, 3, "clock set N | clock advance DURATION | clock show")
    sub = toks[1]
    if sub == "show" and len(toks) == 2:
        pass
    elif sub == "set" and len(toks) == 3:
        sess.clock.set(clock.parse_int(toks[2], "time"))
    elif sub == "advance" and len(toks) == 3:
        sess.clock.advance(clock.parse_duration(toks[2]))
    else:
        raise UsageError("usage: clock set N | clock advance DURATION | clock show")
    sess.emit("CLOCK %d" % sess.clock.now)


# ---------------------------------------------------------------- secrets and attributes
def cmd_secret(sess, line, toks, more):
    _need(toks, 2, 4, "secret add NAME VALUE | secret list")
    if toks[1] == "list" and len(toks) == 2:
        if not sess.secrets:
            sess.emit("no secrets")
        for name in sorted(sess.secrets):
            sess.emit("SECRET %s" % name)
        return
    if toks[1] != "add" or len(toks) != 4:
        raise UsageError("usage: secret add NAME VALUE | secret list")
    name = _name(toks[2], "secret name")
    value = toks[3]
    if name in sess.secrets:
        raise SecretError("secret %s already exists" % name)
    if len(value) < limits.MIN_SECRET_LEN:
        raise SecretError("secret value shorter than %d characters" % limits.MIN_SECRET_LEN)
    sess.secrets[name] = value
    sess.emit("OK secret %s" % name)


def cmd_attr(sess, line, toks, more):
    if len(toks) >= 2 and toks[1] == "show":
        _need(toks, 3, 3, "attr show SUBJECT")
        subject = _subject(toks[2])
        attrs = sess.subjects.get(subject, {})
        text = " ".join("%s=%s" % (k, attrs[k]) for k in sorted(attrs))
        sess.emit(redact.scrub(sess, ("ATTR %s %s" % (subject, text)).rstrip()))
        return
    if len(toks) < 5 or toks[1] != "set":
        raise UsageError("usage: attr set SUBJECT KEY VALUE | attr show SUBJECT")
    subject = _subject(toks[2])
    key = _name(toks[3], "attribute name")
    value = _rest(line, 4)
    sess.subjects.setdefault(subject, {})[key] = value
    sess.emit("OK attr %s.%s" % (subject, key))


# ---------------------------------------------------------------- sets and rules
def cmd_set(sess, line, toks, more):
    if len(toks) < 2:
        raise UsageError("usage: set create|list|show|parent ...")
    sub = toks[1]
    store = sess.store
    if sub == "create":
        _need(toks, 3, 5, "set create NAME [parent=P] [mode=standard|admin]")
        opts = _options(toks[3:], ("parent", "mode"))
        store.create(toks[2], opts.get("parent"), opts.get("mode", "standard"))
        sess.emit("OK set %s" % toks[2])
    elif sub == "list":
        _need(toks, 2, 2, "set list")
        if not store.sets:
            sess.emit("no sets")
        for name in sorted(store.sets):
            pset = store.sets[name]
            sess.emit("SET %s mode=%s parent=%s rules=%d" % (
                name, pset.mode, pset.parent or "-", len(pset.rules)))
    elif sub == "show":
        _need(toks, 3, 3, "set show NAME")
        pset = store.get(toks[2])
        chain = [s.name for s in store.chain(pset.name)]
        sess.emit("SET %s mode=%s chain=%s" % (pset.name, pset.mode, ">".join(chain)))
        for rule in pset.rules:
            sess.emit(redact.scrub(sess, "  %s %s" % (rule.label(), rule.spec())))
    elif sub == "parent":
        _need(toks, 4, 4, "set parent NAME PARENT|-")
        parent = None if toks[3] == "-" else store.get(toks[3]).name
        store.reparent(toks[2], parent)
        sess.emit("OK set %s parent=%s" % (toks[2], parent or "-"))
    else:
        raise UsageError("usage: set create|list|show|parent ...")


def cmd_rule(sess, line, toks, more):
    if len(toks) >= 2 and toks[1] == "del":
        _need(toks, 3, 3, "rule del RID")
        rule = sess.store.remove_rule(policies.parse_rule_id(toks[2]))
        sess.emit("OK deleted %s" % rule.label())
        return
    if len(toks) < 6 or toks[1] != "add":
        raise UsageError("usage: rule add SET EFFECT ACTION RESOURCE [when CONDITION]")
    cond = ""
    if len(toks) > 6:
        if toks[6] != "when":
            raise UsageError("usage: rule add SET EFFECT ACTION RESOURCE [when CONDITION]")
        cond = _rest(line, 7)
        if not cond:
            raise UsageError("empty condition")
    rule = sess.store.add_rule(toks[2], toks[3], toks[4], toks[5], cond, sess.macros)
    sess.emit("OK %s" % rule.label())


def cmd_cond(sess, line, toks, more):
    if len(toks) == 2 and toks[1] == "list":
        if not sess.macros.items:
            sess.emit("no conditions")
        for name in sess.macros.names():
            sess.emit(redact.scrub(sess, "COND %s: %s" % (name, sess.macros.get(name).text)))
        return
    if len(toks) < 4 or toks[1] != "define":
        raise UsageError("usage: cond define NAME EXPR | cond list")
    macro = sess.macros.define(toks[2], _rest(line, 3))
    sess.emit("OK cond %s" % macro.name)


# ---------------------------------------------------------------- evaluation
def cmd_eval(sess, line, toks, more):
    text = _rest(line, 1)
    if not text:
        raise UsageError("usage: eval EXPR")
    ast = macros.compile_condition(sess.macros, text)
    budget = Budget(limits.EVAL_STEPS)
    value = evaluator.evaluate(ast, evaluator.Context(sess), budget)
    sess.emit(redact.scrub(sess, "RESULT %s steps=%d" % (evaluator.format_value(value),
                                                         budget.used)))


def _request(toks, usage):
    if len(toks) < 5:
        raise UsageError("usage: " + usage)
    return toks[1], _subject(toks[2]), toks[3], toks[4], _attrs(toks[5:])


def cmd_check(sess, line, toks, more):
    set_name, subject, action, resource, attrs = _request(
        toks, "check SET SUBJECT ACTION RESOURCE [KEY=VALUE ...]")
    decision = decide.check(sess, set_name, subject, action, resource, attrs)
    sess.emit(decision.line())


def cmd_explain(sess, line, toks, more):
    set_name, subject, action, resource, attrs = _request(
        toks, "explain SET SUBJECT ACTION RESOURCE [KEY=VALUE ...]")
    sess.emit_all(decide.explain(sess, set_name, subject, action, resource, attrs))


# ---------------------------------------------------------------- approvals
def cmd_approve(sess, line, toks, more):
    if len(toks) < 2:
        raise UsageError("usage: approve request|grant|revoke|extend|list ...")
    sub = toks[1]
    if sub == "request":
        _need(toks, 6, 6, "approve request SUBJECT ACTION RESOURCE DURATION")
        subject = _subject(toks[2])
        ttl = clock.parse_duration(toks[5])
        item = approvals.request(sess, subject, toks[3], toks[4], ttl)
        sess.emit("OK %s pending until=%d" % (item.label(), item.expires_at))
    elif sub == "grant":
        _need(toks, 4, 4, "approve grant AID APPROVER")
        item = approvals.grant(sess, toks[2], _subject(toks[3]))
        sess.emit("OK %s approved by=%s" % (item.label(), item.approver))
    elif sub == "revoke":
        _need(toks, 3, 3, "approve revoke AID")
        item = approvals.revoke(sess, toks[2])
        sess.emit("OK %s revoked" % item.label())
    elif sub == "extend":
        _need(toks, 4, 4, "approve extend AID DURATION")
        seconds = clock.parse_duration(toks[3])
        item = approvals.extend(sess, toks[2], seconds)
        sess.emit("OK %s until=%d" % (item.label(), item.expires_at))
    elif sub == "list":
        _need(toks, 2, 2, "approve list")
        lines = approvals.listing(sess)
        if not lines:
            sess.emit("no approvals")
        sess.emit_all(lines)
    else:
        raise ApprovalError("unknown approval command %s" % sub)


# ---------------------------------------------------------------- log, reports, stats
_FILTER_KEYS = ("subject", "effect", "set", "resource", "action")


def _filter_entries(entries, opts):
    out = []
    for e in entries:
        if "subject" in opts and e.subject != opts["subject"]:
            continue
        if "effect" in opts and e.effect != opts["effect"]:
            continue
        if "set" in opts and e.set_name != opts["set"]:
            continue
        if "resource" in opts and not patterns.match_resource(opts["resource"], e.resource):
            continue
        if "action" in opts and not patterns.match_action(opts["action"], e.action):
            continue
        out.append(e)
    return out


def cmd_log(sess, line, toks, more):
    if len(toks) < 2:
        raise UsageError("usage: log show [N] | log filter KEY=VALUE ... | log replay SEQ"
                         " | log retain N")
    sub = toks[1]
    if sub == "show":
        _need(toks, 2, 3, "log show [N]")
        entries = sess.log.ordered()
        if len(toks) == 3:
            n = clock.parse_int(toks[2], "count")
            entries = entries[-n:] if n else []
        lines = [render.text_line(sess, e) for e in entries]
    elif sub == "filter":
        opts = _options(toks[2:], _FILTER_KEYS)
        if not opts:
            raise UsageError("usage: log filter KEY=VALUE ...")
        if "resource" in opts:
            patterns.check_resource(opts["resource"])
        if "action" in opts:
            patterns.check_action(opts["action"])
        lines = [render.text_line(sess, e) for e in _filter_entries(sess.log.ordered(), opts)]
    elif sub == "replay":
        _need(toks, 3, 3, "log replay SEQ")
        seq = toks[2][1:] if toks[2].startswith("#") else toks[2]
        entry = sess.log.get(clock.parse_int(seq, "sequence number"))
        if entry.set_name not in sess.store.sets:
            raise LogError("set %s no longer exists" % entry.set_name)
        now = decide.decide(sess, entry.set_name, entry.subject, entry.action, entry.resource,
                            entry.attrs, use_approvals=False)
        sess.emit("REPLAY #%d was=%s now=%s by=%s" % (entry.seq, entry.effect, now.effect,
                                                       now.by))
        return
    elif sub == "retain":
        _need(toks, 3, 3, "log retain N")
        sess.log.retain(clock.parse_int(toks[2], "count"))
        sess.emit("OK retain %d" % sess.log.keep)
        return
    else:
        raise UsageError("usage: log show [N] | log filter KEY=VALUE ... | log replay SEQ"
                         " | log retain N")
    if not lines:
        sess.emit("no entries")
    sess.emit_all(lines)


def cmd_report(sess, line, toks, more):
    _need(toks, 2, 3, "report FORMAT [TEMPLATE]")
    sess.emit_all(render.report(sess, toks[1], toks[2] if len(toks) == 3 else None))


def cmd_template(sess, line, toks, more):
    if len(toks) == 2 and toks[1] == "list":
        if not sess.templates:
            sess.emit("no templates")
        for name in sorted(sess.templates):
            sess.emit("TEMPLATE %s: %s" % (name, sess.templates[name].text))
        return
    if len(toks) < 4 or toks[1] != "set":
        raise TemplateError("usage: template set NAME TEXT | template list")
    tpl = template.compile_template(toks[2], _rest(line, 3))
    sess.templates[tpl.name] = tpl
    sess.emit("OK template %s" % tpl.name)


def cmd_stats(sess, line, toks, more):
    _need(toks, 1, 1, "stats")
    sess.emit_all(stats.stats_lines(sess))


# ---------------------------------------------------------------- bundles
def _read_block(more):
    block = []
    for raw in more:
        if raw.strip() == ".end":
            return block
        block.append(raw)
    raise UsageError("block not terminated by .end")


def cmd_bundle(sess, line, toks, more):
    if len(toks) == 3 and toks[1] == "export":
        sess.emit_all(bundle.export_lines(sess, toks[2]))
        return
    if len(toks) >= 2 and toks[1] == "import":
        block = _read_block(more)
        if len(toks) != 3:
            raise UsageError("usage: bundle import SET   (block up to .end)")
        header, added = bundle.import_lines(sess, toks[2], block)
        span = "-" if not added else (
            added[0].label() if len(added) == 1 else "%s-%s" % (added[0].label(),
                                                              added[-1].label()))
        sess.emit("OK imported %d rule%s from %s into %s (%s)" % (
            len(added), "" if len(added) == 1 else "s", header["name"], toks[2], span))
        return
    raise UsageError("usage: bundle export SET | bundle import SET")


def cmd_whatif(sess, line, toks, more):
    if len(toks) != 3:
        _read_block(more)
        raise UsageError("usage: whatif SET_A SET_B   (block up to .end)")
    block = _read_block(more)
    sess.emit_all(whatif.compare(sess, toks[1], toks[2], block))


def cmd_lint(sess, line, toks, more):
    _need(toks, 2, 2, "lint SET")
    sess.emit_all(redact.scrub(sess, x) for x in lint.lint_lines(sess, toks[1]))


def cmd_help(sess, line, toks, more):
    _need(toks, 1, 2, "help [COMMAND]")
    sess.emit_all(helptext.help_lines(toks[1] if len(toks) == 2 else None))


def cmd_verify(sess, line, toks, more):
    _need(toks, 1, 1, "verify")
    sess.emit("OK consistent")


COMMANDS = {
    "clock": cmd_clock,
    "secret": cmd_secret,
    "attr": cmd_attr,
    "set": cmd_set,
    "rule": cmd_rule,
    "cond": cmd_cond,
    "eval": cmd_eval,
    "check": cmd_check,
    "explain": cmd_explain,
    "approve": cmd_approve,
    "log": cmd_log,
    "report": cmd_report,
    "template": cmd_template,
    "stats": cmd_stats,
    "bundle": cmd_bundle,
    "whatif": cmd_whatif,
    "lint": cmd_lint,
    "help": cmd_help,
    "verify": cmd_verify,
}


def execute(sess, line, more):
    toks = line.split()
    handler = COMMANDS.get(toks[0])
    if handler is None:
        raise UsageError("unknown command %s" % toks[0])
    handler(sess, line, toks, more)
