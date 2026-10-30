#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all defects), the K=12
mutants (gold plus exactly one defect each) and the patch trees of the
scorer controls from private/gold.  Deterministic, stdlib only.  Every edit
is an exact, unique text replacement, so a drift in gold fails loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D01_PARSE_LIST_DEPTH = [("parser.py", '''    def _list(self):
        self._enter()
        try:
            items = self._items("]")
        finally:
            self._leave()
        if len(items)''', '''    def _list(self):
        items = self._items("]")
        if len(items)''')]

D02_MACRO_BUDGET = [("evaluator.py", '''        return _eval(macro.ast, ctx, budget)
''', '''        return evaluate(macro.ast, ctx)
''')]

D03_EXTEND_EXPIRED = [("approvals.py", '''    _require_live(item, now, LIVE_STATES)
    new_deadline''', '''    _require_state(item, LIVE_STATES)
    new_deadline''')]

D04_EXPIRY_BOUNDARY = [("clock.py", '''    """True once NOW has reached DEADLINE (validity is [start, deadline))."""
    return now >= deadline
''', '''    """True once NOW is past DEADLINE."""
    return now > deadline
''')]

D05_REPORT_PCT = [("render.py", '''    pct = numfmt.pct1(allowed, total) if total else "-"
''', '''    pct = "%.1f" % (100.0 * allowed / total) if total else "-"
''')]

D06_APPROVAL_MATCH = [("approvals.py", '''import clock
import limits
''', '''import clock
import fnmatch
import limits
'''), ("approvals.py", '''    return (patterns.match_action(item.action, action)
            and patterns.match_resource(item.resource, resource))
''', '''    return (fnmatch.fnmatchcase(action, item.action)
            and fnmatch.fnmatchcase(resource, item.resource))
''')]

D07_PATTERN_PREFIX = [("patterns.py", '''        return value == base or value.startswith(base + "/")
''', '''        return value.startswith(base)
''')]

D08_LOG_ORDER = [("decisionlog.py", '''    return (entry.time, entry.seq)
''', '''    return entry.time
''')]

D09_NOTE_REDACTION = [("decide.py", '''        note = "%s: %s" % (rule.label(), redact.scrub(sess, exc.message))
''', '''        note = "%s: %s" % (rule.label(), exc.message)
''')]

D10_HTML_REDACT_ORDER = [("render.py", '''        f = redact.scrub_all(sess, _fields(sess, e, "html"))
        row = "".join(_html_cell(c, f[c]) for c in COLUMNS)
        lines.append("<tr>" + row + "</tr>")
''', '''        f = _fields(sess, e, "html")
        row = "".join(_html_cell(c, f[c]) for c in COLUMNS)
        lines.append(redact.scrub(sess, "<tr>" + row + "</tr>"))
''')]

D11_BUNDLE_MODE = [("bundle.py", '''    mode = target.mode
''', '''    mode = header.get("mode", target.mode)
''')]

D12_CONTEXT_ESCAPE = [("render.py", '''def _context(entry):
    return "; ".join("%s=%s" % (key, entry.attrs[key]) for key in sorted(entry.attrs))
''', '''def _context(entry, fmt):
    pairs = ["%s=%s" % (key, entry.attrs[key]) for key in sorted(entry.attrs)]
    if fmt == "html":
        pairs = [escape.html(p) for p in pairs]
    return "; ".join(pairs)
'''), ("render.py", '''        "context": _context(entry),
''', '''        "context": _context(entry, fmt),
'''), ("render.py", '''def _html_cell(column, value):
    return''', '''def _html_cell(column, value):
    if column == "context":
        return "<td class=\\"%s\\">%s</td>" % (column, value)
    return''')]

DEFECTS = {
    "M01_parse_list_depth": D01_PARSE_LIST_DEPTH,
    "M02_macro_budget": D02_MACRO_BUDGET,
    "M03_extend_expired": D03_EXTEND_EXPIRED,
    "M04_expiry_boundary": D04_EXPIRY_BOUNDARY,
    "M05_report_pct": D05_REPORT_PCT,
    "M06_approval_match": D06_APPROVAL_MATCH,
    "M07_pattern_prefix": D07_PATTERN_PREFIX,
    "M08_log_order": D08_LOG_ORDER,
    "M09_note_redaction": D09_NOTE_REDACTION,
    "M10_html_redact_order": D10_HTML_REDACT_ORDER,
    "M11_bundle_mode": D11_BUNDLE_MODE,
    "M12_context_escape": D12_CONTEXT_ESCAPE,
}

# ---------------------------------------------------------------- control-only edits
# Local patch of the pattern defect: the rule-matching call site in decide.py
# gets its own correct check, the shared helper stays wrong (log filter,
# glob() and approvals still use it).
LOCAL_PATTERN = [("decide.py", '''            if patterns.match_action(rule.action, action) and \\
                    patterns.match_resource(rule.resource, resource):
''', '''            if patterns.match_action(rule.action, action) and \\
                    _resource_ok(rule.resource, resource):
'''), ("decide.py", '''def candidates(sess, set_name, action, resource):''', '''def _resource_ok(pattern, value):
    if pattern.endswith("/**") and "*" not in pattern[:-3]:
        base = pattern[:-3]
        return value == base or value.startswith(base + "/")
    return patterns.match_resource(pattern, value)


def candidates(sess, set_name, action, resource):''')]

# Local patch of the boundary defect: the use by a check compares inline,
# the shared clock.expired() helper stays wrong (grant, extend, list).
LOCAL_BOUNDARY = [("approvals.py", '''        _refresh(item, now)
        if item.state != "approved" or item.subject != subject:
            continue
''', '''        _refresh(item, now)
        if item.state != "approved" or item.subject != subject:
            continue
        if now >= item.expires_at:
            continue
''')]

# Over-aggressive "hardening" of decoys (all defects fixed as well).
OA_PRECEDENCE = [("decide.py", '''    winner = _pick(matched, "override")
    if winner is not None:
        return Decision("allow", winner.label(), budget.used, note)
    if use_approvals:''', '''    if _pick(matched, "deny") is not None:
        winner = _pick(matched, "deny")
        return Decision("deny", winner.label(), budget.used, note)
    winner = _pick(matched, "override")
    if winner is not None:
        return Decision("allow", winner.label(), budget.used, note)
    if use_approvals:''')]
OA_REVOKE = [("approvals.py", '''    _refresh(item, sess.clock.now)
    _require_state(item, ("pending", "approved", "expired"))
''', '''    _require_live(item, sess.clock.now, ("pending", "approved"))
''')]
OA_BUDGET = [("budget.py", '''        if self.used > self.limit:
''', '''        if self.used >= self.limit:
''')]
OA_JSON = [("escape.py", '''        elif ord(ch) < 0x20:
''', '''        elif ord(ch) < 0x20 or ord(ch) > 0x7e or ch == "/":
''')]
OA_TEXT = [("render.py", '''    return redact.scrub(sess, line)
''', '''    return escape.html(redact.scrub(sess, line))
''')]

FILES = sorted(f for f in os.listdir(GOLD) if f.endswith(".py") or f in ("build.sh", "README.md"))


def make_tree(dest, edits):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for f in FILES:
        shutil.copy(os.path.join(GOLD, f), os.path.join(dest, f))
    for fname, old, new in edits:
        p = os.path.join(dest, fname)
        with open(p) as fh:
            text = fh.read()
        assert text.count(old) == 1, (dest, fname, old[:60])
        with open(p, "w") as fh:
            fh.write(text.replace(old, new))


def flat(*groups):
    out = []
    for g in groups:
        out.extend(g)
    return out


def main():
    all_defects = flat(*DEFECTS.values())
    make_tree(os.path.join(TASK, "public", "src"), all_defects)
    mroot = os.path.join(HERE, "mutants")
    if os.path.exists(mroot):
        shutil.rmtree(mroot)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mroot, name), edits)
    ctl = os.path.join(HERE, "controls")
    # (d) partial: everything fixed except the two hardest variants
    #     (log merge order and the html context escaping layer).
    make_tree(os.path.join(ctl, "d_partial_all_but_two", "patch"),
              flat(D08_LOG_ORDER, D12_CONTEXT_ESCAPE))
    # (d2) visible-symptom fix only: the defects that end in exit 86 or in
    #      an obviously wrong line are fixed, the quieter ones are not.
    make_tree(os.path.join(ctl, "d2_partial_visible", "patch"),
              flat(D02_MACRO_BUDGET, D05_REPORT_PCT, D06_APPROVAL_MATCH, D07_PATTERN_PREFIX,
                   D08_LOG_ORDER, D12_CONTEXT_ESCAPE, D11_BUNDLE_MODE))
    # (g) local patches where the shared helper had to change
    make_tree(os.path.join(ctl, "g1_local_pattern_patch", "patch"),
              flat(D07_PATTERN_PREFIX, LOCAL_PATTERN))
    make_tree(os.path.join(ctl, "g2_local_boundary_patch", "patch"),
              flat(D04_EXPIRY_BOUNDARY, LOCAL_BOUNDARY))
    # (e) over-aggressive hardening of decoys, all defects fixed
    make_tree(os.path.join(ctl, "e1_overaggressive_precedence", "patch"), OA_PRECEDENCE)
    make_tree(os.path.join(ctl, "e2_overaggressive_revoke", "patch"), OA_REVOKE)
    make_tree(os.path.join(ctl, "e3_overaggressive_budget", "patch"), OA_BUDGET)
    make_tree(os.path.join(ctl, "e4_overaggressive_escaping", "patch"), flat(OA_JSON, OA_TEXT))
    print("public/src, %d mutants and control trees written" % len(DEFECTS))


if __name__ == "__main__":
    main()
