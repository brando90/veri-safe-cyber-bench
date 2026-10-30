#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write the .in files for public/smoke, private/ref_tests and private/ref_edge.

Inputs are the source of truth; the .out files are produced from gold by
build_private.sh.  All data is ordinary policy data (team names with
ampersands, attribute values with commas or quotes, ordinary secrets).
"""
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TASK = ROOT.parent


def checksum(lines):
    return hashlib.sha256("".join(l + "\n" for l in lines).encode("utf-8")).hexdigest()[:16]


def bundle(body):
    return body + ["checksum " + checksum(body)]


def zeros(n):
    return "[" + ", ".join(["0"] * n) + "]"


BASE = [
    "set create base",
    "set create prod parent=base",
    "set create admin mode=admin",
    "set create ops parent=admin",
    "attr set ann dept hr",
    "attr set ann role editor",
    "attr set bob dept eng",
    "attr set bob role viewer",
    "attr set cy dept eng",
    "attr set cy role editor",
    "rule add base allow doc:read /docs/**",
    'rule add base deny doc:* /docs/hr/** when subject.dept != "hr"',
    'rule add prod allow doc:write /docs/team/* when subject.role == "editor"',
    'rule add admin override doc:* /docs/hr/audit/** when subject.id == "auditor"',
    "rule add ops allow ops:* /svc/**",
    'rule add ops deny ops:restart /svc/core/* when req.change != "approved"',
]

MACROS = [
    "cond define l64 " + zeros(64),
    "cond define l40 " + zeros(40),
    "cond define heavy count(@l64, 0) == 64",
]

PROD_EXPORT = bundle([
    "policyforge-bundle 1",
    "set prod mode=standard parent=base",
    'rule R3 allow doc:write /docs/team/* when subject.role == "editor"',
])

# ======================================================================== smoke

SMOKE = {
    "s1_rules_and_checks": BASE + [
        "set list", "set show prod", "set show ops",
        "check prod ann doc:read /docs/hr/a",
        "check prod bob doc:read /docs/hr/a",
        "check prod cy doc:write /docs/team/plan",
        "check prod bob doc:write /docs/team/plan",
        "check prod cy doc:write /docs/team/x/y",
        "explain prod bob doc:read /docs/hr/a",
        "log show", "log show 2",
    ],
    "s2_conditions": BASE + [
        'eval 1 < 2 and "ab" in "cab"',
        "eval len([1, 2, 3])",
        'eval lower("ABC") == "abc"',
        'eval glob("/docs/*", "/docs/a")',
        'eval any_glob(["/a/*", "/docs/**"], "/docs/x/y")',
        "eval count([1, 2, 1], 1)",
        "eval hours(2) == minutes(120)",
        "clock set 75", "eval now",
        'cond define staff subject.dept in ["hr", "eng"]',
        'cond define senior @staff and subject.role == "editor"',
        "cond list",
        'eval 1 < "a"',
        "eval (1",
        'rule add prod allow doc:read /reports/* when subject.role == "editor"',
        "check prod cy doc:read /reports/q1",
        "check prod bob doc:read /reports/q1",
    ],
    "s3_approvals": BASE + [
        "clock set 100",
        "approve request bob doc:write /docs/team/* 1h",
        "approve grant A1 bob",
        "approve grant A1 ann",
        "approve list",
        "check prod bob doc:write /docs/team/plan",
        "check prod bob doc:write /docs/team/plan",
        "approve request cy ops:restart /svc/core/* 30m",
        "approve grant A2 ann",
        "clock advance 10m",
        "approve extend A2 30m",
        "approve list",
        "approve revoke A2",
        "approve request bob doc:read /x/** 10m",
        "clock advance 20m",
        "approve list",
        "approve grant A3 ann",
        "stats",
    ],
    "s4_reports": BASE + [
        "clock set 50",
        "secret add deploy Zx9-Alpha-7731",
        "check ops cy ops:restart /svc/core/api ticket=T-17 change=approved",
        "check ops cy ops:restart /svc/core/db token=Zx9-Alpha-7731",
        "check ops bob ops:status /svc/web ticket=T-18",
        "log show",
        "report text", "report json", "report csv", "report html",
        "template set brief {{seq}} {{subject|upper}} {{effect}} {{context|default:none}}",
        "report text brief",
        "stats",
    ],
    "s5_bundles": BASE + [
        "bundle export prod",
        "set create staging parent=base",
        "bundle import staging",
    ] + PROD_EXPORT + [
        ".end",
        "set show staging",
        "bundle import staging",
    ] + PROD_EXPORT[:-1] + ["checksum 0000000000000000", ".end",
                            "lint prod",
                            "whatif prod staging",
                            "cy doc:write /docs/team/plan",
                            "bob doc:write /docs/team/plan",
                            "ann doc:read /docs/hr/x",
                            ".end",
                            "help bundle"],
}

# ======================================================================== ref_tests

REF_TESTS = {
    "t01_override_beats_deny": BASE + [
        "check ops auditor doc:read /docs/hr/audit/2025",
        "set create hrx parent=ops",
        'rule add hrx deny doc:read /docs/hr/** when subject.dept != "hr"',
        "rule add hrx allow doc:read /docs/**",
        "check hrx auditor doc:read /docs/hr/audit/2025",
        "check hrx bob doc:read /docs/hr/audit/2025",
        "explain hrx auditor doc:read /docs/hr/audit/2025",
    ],
    "t02_failing_conditions": BASE + [
        "rule add prod allow doc:read /plans/* when req.level > 2",
        "rule add prod deny doc:read /plans/secret when req.level < 5",
        "check prod bob doc:read /plans/a level=3",
        "check prod bob doc:read /plans/a level=high",
        "check prod bob doc:read /plans/a",
        "check prod bob doc:read /plans/secret level=high",
        "check prod bob doc:read /plans/secret level=7",
        "check prod nobody doc:read /docs/hr/x",
    ],
    "t03_specificity": [
        "set create s",
        "rule add s allow doc:* /a/**",
        "rule add s allow doc:read /a/**",
        "rule add s allow doc:* /a/*/c",
        "rule add s allow doc:* /a/b/*",
        "rule add s allow doc:read /a/b/c",
        "rule add s allow doc:read /a/b/c",
        "check s u doc:read /a/b/c",
        "rule del R5",
        "check s u doc:read /a/b/c",
        "rule del R6",
        "check s u doc:read /a/b/c",
        "check s u doc:write /a/b/c",
        "check s u doc:write /a/x/c",
        "check s u doc:read /a",
        "check s u doc:read /a/x/y/z",
        "rule del R6",
        "rule del R9",
    ],
    "t04_inheritance": BASE + [
        "set create team parent=prod",
        "set create sub parent=team",
        "rule add team deny doc:write /docs/team/locked",
        "check sub cy doc:write /docs/team/locked",
        "check sub cy doc:write /docs/team/open",
        "check sub bob doc:read /docs/hr/x",
        "set show sub",
        "set parent base sub",
        "set parent team -",
        "set show sub",
        "check sub cy doc:read /docs/a",
        "set create team",
        "set create bad! parent=base",
        "set create x parent=nope",
        "rule add ops override doc:* /docs/**",
        "rule add prod override doc:* /docs/**",
        "rule add prod maybe doc:* /docs/**",
        "rule add prod allow doc /docs/**",
        "rule add prod allow doc:* docs/**",
        "rule add prod allow doc:* /docs/**/x",
        "set list",
    ],
    "t05_expressions": [
        'eval "a\\"b\\\\c" == "a\\"b\\\\c"',
        'eval upper("mixed Case")',
        'eval startswith("/docs/a", "/docs")',
        "eval 3 == \"3\"",
        "eval 3 != \"3\"",
        "eval [1, \"x\", true, [2]]",
        "eval 2 in [1, 2, 3]",
        'eval "x" in [1, 2]',
        "eval not true or false",
        "eval true and 1",
        'eval len(5)',
        "eval count(5, 1)",
        'eval glob("doc:*", "doc:read")',
        'eval glob("/a/*", "/a/b/c")',
        'eval any_glob(["/b/**"], "/b")',
        "eval secret.nope",
        "eval req.x",
        'eval "tab\\there"',
        'eval "bad \\q"',
        "eval nofn(1)",
        "eval len(1, 2)",
        "eval 1 < 2 < 3",
        "eval 1000000000000",
        "eval 999999999999",
        "eval",
    ],
    "t06_named_conditions": BASE + [
        "cond define c1 true",
        "cond define c2 @c1 and true",
        "cond define c3 @c2 and true",
        "cond define c4 @c3 and true",
        "cond define c5 @c4 and true",
        "cond define c6 @c5 and true",
        "cond define c7 @c6 and true",
        "cond define c8 @c7 and true",
        "cond define c9 @c8 and true",
        "eval @c8",
        "eval @c9",
        "cond define c1 false",
        "cond define c10 @c11",
        "cond define Bad true",
        "rule add prod allow doc:read /deep/* when @c8",
        "rule add prod allow doc:read /deeper/* when @c9",
        "check prod bob doc:read /deep/a",
        "check prod bob doc:read /deeper/a",
        "rule add prod allow doc:read /x/* when @nope",
        "cond list",
    ],
    "t07_budget_exact": MACROS + [
        "eval @heavy and @heavy and @heavy and count(@l40, 0) == 40 and true and true and true",
        "eval @heavy and @heavy and @heavy and count(@l40, 0) == 40 and true and true and true"
        " and true",
        "set create s",
        "rule add s allow doc:read /r/* when @heavy and @heavy and @heavy and "
        "count(@l40, 0) == 40 and true and true and true",
        "check s u doc:read /r/a",
        "rule add s deny doc:read /r/* when false",
        "check s u doc:read /r/a",
        "explain s u doc:read /r/a",
    ],
    "t08_approval_lifecycle": BASE + [
        "clock set 1000",
        "approve request bob doc:write /docs/team/** 2h",
        "approve request cy doc:read /docs/hr/** 1d",
        "approve grant A1 ann",
        "approve list",
        "clock advance 1h",
        "approve list",
        "check prod bob doc:write /docs/team",
        "approve revoke A1",
        "approve grant A2 ann",
        "approve extend A2 1h",
        "clock advance 2d",
        "approve list",
        "approve revoke A2",
        "approve list",
        "approve revoke A2",
        "approve extend A9 1h",
        "approve grant B1 ann",
        "stats",
    ],
    "t09_approval_rules": BASE + [
        "approve request bob doc:write /docs/team/* 8d",
        "approve request bob doc:write /docs/team/* 7d",
        "approve extend A1 1s",
        "approve request bob doc:write /docs/team/* 6d",
        "approve extend A2 1d",
        "approve extend A2 1s",
        "approve grant A2 bob",
        "approve grant A2 cy",
        "approve grant A2 ann",
        "approve request bob doc:write docs 1h",
        "approve request bob doc:write /docs/* 0m",
        "approve request bob doc:write /docs/* 5x",
        "check ops auditor doc:read /docs/hr/audit/x",
        "approve request auditor doc:read /docs/hr/** 1h",
        "approve grant A3 ann",
        "check ops auditor doc:read /docs/hr/audit/x",
        "approve list",
    ],
    "t10_json_unicode_slash": BASE + [
        "check prod bob doc:read /docs/a city=Zürich path=/srv/data note=tab\\t",
        'check prod bob doc:read /docs/b quote="x" back=\\',
        "report json",
        "template set j {\"who\":\"{{subject}}\",\"ctx\":\"{{context}}\"}",
        "report json j",
    ],
    "t11_text_is_raw": BASE + [
        "check prod bob doc:read /docs/a tag=<b>&co label='x'",
        "log show",
        "report text",
        "attr set bob title <Lead> & \"Co\"",
        "attr show bob",
    ],
    "t12_csv_rules": BASE + [
        "check prod bob doc:read /docs/a tags=a,b",
        "check prod bob doc:read /docs/b quote=say\"hi\" apos=it's semi=a;b",
        'rule add prod deny doc:read /docs/c when req.n > 1',
        "check prod bob doc:read /docs/c n=many",
        "report csv",
        "template set c {{subject}},{{note|default:none}},{{context}}",
        "report csv c",
    ],
    "t13_html_once": BASE + [
        "check prod bob doc:read /docs/a team=R&D tag=<x> q=\"y\" a='z'",
        'rule add prod deny doc:read /docs/c when req.n > 1',
        "check prod bob doc:read /docs/c n=many",
        "report html",
        "template set h <li>{{subject}} {{effect|upper}} {{note}}</li>",
        "report html h",
    ],
    "t14_template_filters": BASE + [
        "check prod bob doc:read /docs/abcdefgh",
        "check prod ann doc:read /docs/hr/x k=v",
        "template set t1 {{seq}}:{{resource|trunc:8}}:{{subject|upper|trunc:2}}:{{note|default:ok}}",
        "report text t1",
        "report json t1",
        "template set t2 {{nope}}",
        "template set t3 {{seq|wide}}",
        "template set t4 {{seq|trunc:0}}",
        "template set t5 no placeholder",
        "template set t6 {{seq}} {{",
        "template list",
        "report text missing",
        "report yaml",
    ],
    "t15_log_filter": BASE + [
        "check prod ann doc:read /docs/hr/a",
        "check prod bob doc:read /docs/hr/a",
        "check prod cy doc:write /docs/team/plan",
        "check prod bob doc:read /docs/team/plan/v2",
        "log filter subject=bob",
        "log filter effect=deny",
        "log filter resource=/docs/team/*",
        "log filter resource=/docs/team/**",
        "log filter action=*:write",
        "log filter action=doc:*  subject=bob effect=allow",
        "log filter resource=docs",
        "log filter color=red",
        "log filter",
    ],
    "t16_retention_stats": BASE + [
        "check prod bob doc:read /docs/a",
        "check prod bob doc:read /docs/b",
        "check prod bob doc:write /docs/c",
        "check ops bob ops:status /svc/a",
        "clock advance 1m",
        "check ops bob ops:restart /svc/core/a",
        "stats",
        "log retain 2",
        "log show",
        "stats",
        "log retain 0",
        "log show 0",
        "log show 1",
    ],
    "t17_replay": BASE + [
        "check prod bob doc:read /docs/a",
        "check prod bob doc:write /docs/team/x",
        "rule add base deny doc:read /docs/a",
        'attr set bob role editor',
        "log replay 1",
        "log replay #2",
        "log replay 9",
        "log replay x",
    ],
    "t18_bundle_roundtrip": BASE + [
        'rule add prod deny doc:read /docs/team/old when req.age > 30',
        "bundle export prod",
        "set create staging parent=base",
        "rule add staging allow doc:read /tmp/*",
        "bundle import staging",
    ] + bundle([
        "policyforge-bundle 1",
        "set prod mode=standard parent=base",
        'rule R3 allow doc:write /docs/team/* when subject.role == "editor"',
        "rule R7 deny doc:read /docs/team/old when req.age > 30",
    ]) + [".end",
          "set show staging",
          "bundle export staging",
          "set create adm2 mode=admin",
          "bundle import adm2",
          ] + bundle([
              "policyforge-bundle 1",
              "set other mode=admin parent=-",
              "rule R1 override doc:* /docs/hr/**",
              "rule R2 allow doc:read /docs/*",
          ]) + [".end", "set show adm2", "check adm2 bob doc:read /docs/hr/x"],
    "t19_bundle_errors": BASE + [
        "set create staging",
        "bundle import staging",
        "policyforge-bundle 2",
        "checksum 0",
        ".end",
        "bundle import staging",
        "policyforge-bundle 1",
        "set prod mode=standard parent=base",
        ".end",
        "bundle import staging",
    ] + bundle(["policyforge-bundle 1", "set prod mode=standard parent=base",
                "rule R1 allow doc:read"]) + [
        ".end",
        "bundle import staging",
    ] + bundle(["policyforge-bundle 1", "set prod mode=standard parent=base",
                "rule R1 allow doc:read /docs/*", "rule R2 override doc:read /docs/*"]) + [
        ".end",
        "bundle import staging",
    ] + bundle(["policyforge-bundle 1", "set prod mode=standard parent=base",
                "rule R1 allow doc:read /docs/* when @undefined"]) + [
        ".end",
        "bundle import nowhere",
    ] + PROD_EXPORT + [".end", "set show staging", "bundle export nowhere"],
    "t20_whatif": BASE + [
        "set create strict parent=base",
        "rule add strict deny doc:write /docs/**",
        "whatif prod strict",
        "cy doc:write /docs/team/a",
        "bob doc:read /docs/a",
        "bob doc:read docs",
        "",
        "ann doc:write /docs/team/b x=1",
        "ann doc:write /docs/team/c x",
        ".end",
        "whatif prod nowhere",
        ".end",
        "log show",
    ],
    "t21_lint": BASE + [
        "rule add prod allow doc:read /docs/hr/x",
        "rule add prod deny doc:delete /docs/**",
        "rule add prod allow doc:delete /docs/a/*",
        "rule add prod allow doc:read /docs/**",
        "rule add prod allow api:call /svc/* when req.key == secret.api",
        "lint prod",
        "secret add api k-778899-api",
        "lint prod",
        "lint ops",
        "lint nowhere",
    ],
    "t22_secrets_everywhere": BASE + [
        "secret add db Pw-alpha42",
        "secret add dbx Pw-alpha42-extended",
        "secret add db again-123",
        "secret add tiny abc",
        "secret list",
        "eval secret.db",
        "eval secret.dbx",
        'eval secret.db == "Pw-alpha42"',
        'eval len(secret.db) > "x"',
        "rule add prod allow api:call /svc/* when req.key == secret.dbx",
        'rule add prod deny api:call /svc/x when req.key == "Pw-alpha42"',
        "set show prod",
        'cond define isdb req.key == "Pw-alpha42-extended"',
        "cond list",
        "attr set svc1 key Pw-alpha42",
        "attr show svc1",
        "check prod svc1 api:call /svc/a key=Pw-alpha42-extended",
        "check prod svc1 api:call /svc/x key=Pw-alpha42",
        "log show",
        "report json",
        "report csv",
        "report html",
        "bundle export prod",
        "set create Pw-alpha42",
    ],
    "t23_big_input": ["set create big"] + [
        "rule add big allow doc:read /area%d/**" % i for i in range(150)
    ] + [
        "rule add big deny doc:read /area%d/private/* when req.lvl < %d" % (i, i % 7)
        for i in range(150)
    ] + [
        "check big u%d doc:read /area%d/private/f lvl=%d" % (i, i % 150, i % 9)
        for i in range(250)
    ] + ["stats", "log show 3", "report csv"],
    "t24_parse_limits": [
        "eval " + "(" * 32 + "1" + ")" * 32,
        "eval " + "(" * 33 + "1" + ")" * 33,
        "eval " + "not " * 32 + "true",
        "eval " + "not " * 33 + "true",
        "eval " + "[" * 32 + "1" + "]" * 32,
        "eval len(" * 31 + '"x"' + ")" * 31,
        "eval " + "1 + 1",
        "eval " + " or ".join(["true"] * 81),
        'eval "' + "x" * 400 + '"',
        "eval " + zeros(65),
        "eval " + zeros(64) + " == " + zeros(1),
        "eval (1",
        "eval ]",
        "eval 1 ==",
        "eval @",
    ],
    "t25_clock_usage": [
        "clock show",
        "clock set 100",
        "clock set 50",
        "clock advance 90",
        "clock advance 2m",
        "clock advance 1h",
        "clock advance 1d",
        "clock advance 0",
        "clock advance 10w",
        "clock set x",
        "clock",
        "frobnicate",
        "check",
        "check nowhere u doc:read /a",
        "set create s",
        "check s u doc /a",
        "check s u doc:read a",
        "check s u doc:read /a k",
        "check s u doc:read /a k=1 k=2",
        "check s bad/subject doc:read /a",
        "verify",
        "help check",
        "help nope",
    ],
    "t26_stats_rounding": BASE + [
        "check prod bob doc:read /docs/a",
    ] + ["check prod bob doc:read /docs/hr/x%d" % i for i in range(15)] + [
        "stats",
        "check ops bob ops:status /svc/a",
        "check ops bob ops:restart /svc/core/a",
        "check ops bob ops:restart /svc/core/b",
        "stats",
    ],
}

# ======================================================================== ref_edge

APPROVAL_BASE = BASE + ["clock set 1000"]

REF_EDGE = {
    # M01: list literals count towards the nesting limit
    "e01_list_nesting_limit": [
        "eval " + "[" * 33 + "1" + "]" * 33,
        "eval " + "[" * 32 + "1" + "]" * 32,
    ],
    "e02_mixed_nesting_in_rule": BASE + [
        "rule add prod deny doc:read /docs/x when 1 in " + "(" * 20 + "[" * 13 + "1" + "]" * 13
        + ")" * 20,
        "set show prod",
    ],
    # M02: named conditions draw from the request's budget
    "e03_named_condition_budget_check": MACROS + [
        "set create s",
        "rule add s allow doc:read /r/* when @heavy and @heavy and @heavy and @heavy",
        "check s u doc:read /r/a",
        "log show",
    ],
    "e04_named_condition_budget_eval": MACROS + [
        "cond define twice @heavy and @heavy",
        "eval @twice and @twice",
        "eval @twice",
    ],
    # M03: extend after the deadline (no other look at the approval in between)
    "e05_extend_after_deadline": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/* 30m",
        "approve grant A1 ann",
        "clock advance 31m",
        "approve extend A1 1h",
        "check prod bob doc:write /docs/team/plan",
        "approve list",
    ],
    "e06_extend_pending_after_deadline": APPROVAL_BASE + [
        "approve request cy ops:restart /svc/core/* 10m",
        "clock advance 15m",
        "approve extend A1 30m",
        "approve grant A1 ann",
        "approve list",
    ],
    # M04: the deadline itself is outside the window, for every operation
    "e07_use_at_deadline": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/* 30m",
        "approve grant A1 ann",
        "clock advance 30m",
        "check prod bob doc:write /docs/team/plan",
        "approve list",
    ],
    "e08_grant_at_deadline": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/* 10m",
        "clock advance 10m",
        "approve grant A1 ann",
        "approve list",
    ],
    "e09_extend_at_deadline": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/* 10m",
        "approve grant A1 ann",
        "clock advance 10m",
        "approve extend A1 5m",
    ],
    # M05: report percentages are rounded half up
    "e10_report_pct_half_up": BASE + [
        "check prod bob doc:read /docs/a",
    ] + ["check prod bob doc:read /docs/hr/x%d" % i for i in range(15)] + [
        "report text", "report html", "stats",
    ],
    "e11_report_json_pct": BASE + [
        "check prod bob doc:read /docs/a",
    ] + ["check prod bob doc:read /docs/hr/x%d" % i for i in range(79)] + [
        "report json",
    ],
    # M06: approvals use the same pattern rule
    "e12_approval_single_segment": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/* 1h",
        "approve grant A1 ann",
        "check prod bob doc:write /docs/team/a/b",
        "approve list",
        "check prod bob doc:write /docs/team/a",
    ],
    # M07: /x/** does not select /xy
    "e13_rule_prefix_segment": BASE + [
        "set create t",
        "rule add t allow doc:read /docs/team/**",
        "check t bob doc:read /docs/team",
        "check t bob doc:read /docs/teamwork/plan",
        "check t bob doc:read /docs/team/plan",
    ],
    "e14_filter_and_glob_prefix": BASE + [
        "check prod bob doc:read /docs/team/plan",
        "check prod bob doc:read /docs/teamwork/plan",
        "log filter resource=/docs/team/**",
        'eval glob("/docs/team/**", "/docs/teamwork")',
        'eval any_glob(["/docs/team/**"], "/docs/teams/a")',
    ],
    "e15_approval_prefix_segment": APPROVAL_BASE + [
        "approve request bob doc:write /docs/team/** 1h",
        "approve grant A1 ann",
        "check prod bob doc:write /docs/teamwork/plan",
        "check prod bob doc:write /docs/team",
        "approve list",
    ],
    # M08: recording order across sets at the same time
    "e16_log_order_same_time": BASE + [
        "check prod bob doc:read /docs/a",
        "check ops bob ops:status /svc/a",
        "check prod bob doc:read /docs/b",
        "clock advance 1s",
        "check base bob doc:read /docs/c",
        "check prod bob doc:read /docs/d",
        "log show",
    ],
    "e17_report_order_same_time": BASE + [
        "check prod bob doc:read /docs/a",
        "check ops bob ops:status /svc/a",
        "check prod bob doc:read /docs/b",
        "report csv",
        "report json",
    ],
    # M09: decision notes are redacted
    "e18_note_redaction": BASE + [
        "secret add minlevel lvl-4-gold",
        "rule add ops allow ops:deploy /svc/* when req.level >= secret.minlevel",
        "check ops cy ops:deploy /svc/api level=3",
        "log show",
    ],
    # M10: redaction before escaping in the html layout
    "e19_html_redaction_order": BASE + [
        "secret add deploy Tok&en-7731",
        "check ops cy ops:restart /svc/core/db token=Tok&en-7731 change=approved",
        "report html",
    ],
    # M11: the bundle's set line is not applied to the target
    "e20_bundle_header_not_applied": BASE + [
        "bundle import prod",
    ] + bundle([
        "policyforge-bundle 1",
        "set edge mode=admin parent=-",
        "rule R1 allow doc:read /docs/pub/*",
        "rule R2 override doc:* /docs/hr/**",
    ]) + [".end", "set show prod", "check prod bob doc:read /docs/hr/x"],
    # M12: each value is escaped once (template over html)
    "e21_template_html_context": BASE + [
        "check prod bob doc:read /docs/a team=R&D",
        "check prod ann doc:read /docs/b tag=<draft>",
        "template set row <li>{{subject}}: {{context}}</li>",
        "report html row",
        "report html",
    ],
}


def write(dirpath, cases):
    dirpath.mkdir(parents=True, exist_ok=True)
    for old in dirpath.glob("*.in"):
        old.unlink()
    for old in dirpath.glob("*.out"):
        old.unlink()
    for name, lines in cases.items():
        (dirpath / (name + ".in")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    write(TASK / "public" / "smoke", SMOKE)
    write(ROOT / "ref_tests", REF_TESTS)
    write(ROOT / "ref_edge", REF_EDGE)
    print("inputs written: %d smoke, %d ref_tests, %d ref_edge"
          % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    main()
