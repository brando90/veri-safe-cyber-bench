#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Write every .in file of public/smoke, private/ref_tests and private/ref_edge.

Hand-written cases are listed below.  The generated sessions come from a
seeded random generator.  "Ordinary" sessions (ref_tests) are accepted only
when the gold tree, the original and every mutant agree on them and exit
cleanly (rejection sampling, deterministic for the fixed seeds); "hazard"
sessions (ref_edge) are accepted only when the original gets them wrong.
The expected .out files are made by build_private.sh from the gold tree.
"""
import os
import random
from datetime import datetime, timedelta
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")
ORIG = os.path.join(TASK, "public", "src")
MUTANTS = os.path.join(HERE, "mutants")
sys.dont_write_bytecode = True

NOW = "now 2026-03-10T12:00:00Z"


def write(directory, name, lines):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, name + ".in"), "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def log(ts, src, user, *fields, msg=None):
    text = "log %s %s %s" % (ts, src, user)
    if fields:
        text += " " + " ".join(fields)
    if msg is not None:
        text += " -- " + msg
    return text


# ---------------------------------------------------------------- running trees
def run_tree(tree, lines):
    data = ("\n".join(lines) + "\n").encode()
    with tempfile.TemporaryDirectory() as cwd:
        res = subprocess.run([sys.executable, os.path.join(tree, "main.py")], input=data, cwd=cwd,
                             capture_output=True, timeout=20,
                             env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                  "PYTHONHASHSEED": "0", "LC_ALL": "C.UTF-8",
                                  "PYTHONDONTWRITEBYTECODE": "1", "HOME": cwd})
    clean = res.returncode == 0 and b"INVARIANT:" not in res.stderr and b"Traceback" not in res.stderr
    return clean, res.stdout


def all_trees():
    trees = [ORIG]
    trees += [os.path.join(MUTANTS, m) for m in sorted(os.listdir(MUTANTS))]
    return trees


def agrees_everywhere(lines):
    ok, gold_out = run_tree(GOLD, lines)
    if not ok:
        return False
    for tree in all_trees():
        clean, out = run_tree(tree, lines)
        if not clean or out != gold_out:
            return False
    return True


def original_fails(lines):
    ok, gold_out = run_tree(GOLD, lines)
    clean, out = run_tree(ORIG, lines)
    return ok and not (clean and out == gold_out)


# ---------------------------------------------------------------- generator
SOURCES = ["auth", "web", "db", "batch", "mail", "api"]
USERS = ["alice@example.com", "bob", "carol@corp.test", "dave@example.com", "erin", "frank@corp.test"]
LEVELS = ["error", "warn", "info", "debug", "notice"]
ZONES = ["Z", "+0200", "-0500", "+0530", "", "-0330", "+0100"]
PLAIN_NAMES = ["level", "ip", "path", "bytes", "session", "x-trace", "ua", "x-forwarded", "note",
               "api-key", "password", "region"]
HAZARD_NAMES = ["xid", "xff", "x-xhop", "x-secret", "token", "secret"]
LETTERS = "abcdefghijklmnopqrstuvwxyz0123456789"


class Gen:
    def __init__(self, seed, hazard=0.0, size=60):
        self.rng = random.Random(seed)
        self.hazard = hazard
        self.size = size
        self.lines = []
        self.count = 0

    def hz(self):
        return self.rng.random() < self.hazard

    def word(self, lo=4, hi=14):
        return "".join(self.rng.choice(LETTERS) for _ in range(self.rng.randint(lo, hi)))

    def stamp(self, now_day):
        old = self.rng.random() < (0.45 if self.hazard else 0.06)
        back = self.rng.randint(8, 44) if old else self.rng.randint(0, 5)
        when = datetime(2026, 3, 10, 12, 0, 0) - timedelta(days=back, seconds=self.rng.randint(0, 86399))
        if self.rng.random() < 0.04:
            when = datetime(2026, 3, 10, 12, 0, 0) + timedelta(seconds=self.rng.randint(1, 200000))
        return when.strftime("%Y-%m-%dT%H:%M:%S") + self.rng.choice(ZONES)

    def value(self, name):
        if name == "level":
            return self.rng.choice(LEVELS)
        if name == "bytes":
            return str(self.rng.randint(0, 99999)) if self.rng.random() < 0.9 else ""
        if name in ("api-key", "password", "token", "secret"):
            v = self.word(8, 16)
            if self.hz():
                v = self.rng.choice([self.word(1, 3), v + "==", v[:5] + "=" + v[5:]])
            return v
        v = self.word(2 if self.hz() else 5, 12)
        if self.hz():
            v += "=" + self.word(1, 4)
        return v

    def message(self):
        parts = [self.word(3, 8) for _ in range(self.rng.randint(0, 5))]
        pairs = self.rng.randint(0, 3 if self.hz() else 2)
        for _ in range(pairs):
            key = self.rng.choice(["password", "token", "secret", "apikey", "passwd"])
            if self.hz():
                key = key.capitalize()
            val = self.word(1 if self.hz() else 6, 10)
            parts.insert(self.rng.randint(0, len(parts)), "%s=%s" % (key, val))
        if self.rng.random() < 0.3:
            parts.append("tok_" + self.word(8, 14))
        return " ".join(parts)

    def log_line(self, now_day):
        names = list(PLAIN_NAMES)
        if self.hazard:
            names += HAZARD_NAMES
        chosen = sorted(set(self.rng.sample(names, self.rng.randint(0, 5))))
        fields = ["%s=%s" % (n, self.value(n)) for n in chosen]
        text = "log %s %s %s" % (self.stamp(now_day), self.rng.choice(SOURCES), self.rng.choice(USERS))
        if fields:
            text += " " + " ".join(fields)
        if self.rng.random() < 0.7:
            text += " -- " + self.message()
        return text

    def rule_line(self):
        action = self.rng.choice(["redact", "mask", "drop", "pseudo", "keep"])
        name = self.rng.choice(PLAIN_NAMES + (HAZARD_NAMES if self.hazard else []))
        if self.rng.random() < 0.15:
            prefixes = ["sess", "api", "pass", "no"]
            return "rule prefix %s %s" % (self.rng.choice(prefixes),
                                          self.rng.choice(["redact", "mask", "drop"]))
        return "rule %s %s" % (action, name)

    def session(self):
        out = [NOW, "retain %d" % self.rng.choice([7, 14, 30]), "window %d" % self.rng.choice([30, 60, 600]),
               "limit * %d" % self.rng.randint(1 if self.hazard else 2, 6), "salt pepper"]
        if self.hazard and self.hz():
            out.append("limit %s 0" % self.rng.choice(SOURCES))
        for _ in range(self.rng.randint(1, 4)):
            out.append(self.rule_line())
        if self.rng.random() < 0.4:
            out.append("strict on")
            out.append("rule keep level")
        seen_prefix = sum(1 for l in out if l.startswith("rule prefix"))
        if not self.hazard and seen_prefix > 1:
            out = [l for l in out if not l.startswith("rule prefix")][:]
        for _ in range(self.size):
            r = self.rng.random()
            if r < 0.62:
                out.append(self.log_line(10 + self.rng.randint(0, 18)))
            elif r < 0.70:
                out.append("export" + (" " + self.rng.choice(SOURCES) if self.rng.random() < 0.4 else ""))
            elif r < 0.78:
                out.append("report" if self.hazard else "days")
            elif r < 0.84:
                out.append("purge")
            elif r < 0.88:
                out.append("now 2026-03-%02dT%02d:00:00Z" % (self.rng.randint(8, 28), self.rng.randint(0, 23)))
            elif r < 0.91:
                out.append(self.rng.choice(["days", "stats", "rules"] if self.hazard else ["days", "rules"]))
            elif r < 0.95:
                out.append("show %s%d" % (self.rng.choice(["", "#"]), self.rng.randint(1, 30)))
            elif r < 0.98:
                out.append(self.rule_line())
            else:
                out.append("limit %s %d" % (self.rng.choice(SOURCES), self.rng.randint(1, 4)))
        if self.hazard and self.hz():
            out.append("export keep=ip,note")
            out.append("export")
        if self.hazard:
            out.append("report")
        out.append("check")
        return out


def ordinary_session(seed):
    """The first seed at or after SEED whose session every tree agrees on."""
    for attempt in range(400):
        lines = Gen(seed * 1000 + attempt, 0.0, 70).session()
        if agrees_everywhere(lines):
            return lines
    raise SystemExit("no ordinary session for seed %d" % seed)


def hazard_session(seed, hazard=0.35):
    for attempt in range(400):
        lines = Gen(seed * 1000 + attempt, hazard, 70).session()
        if original_fails(lines):
            return lines
    raise SystemExit("no hazard session for seed %d" % seed)


# ---------------------------------------------------------------- smoke
def smoke():
    s = {}
    s["s1_basic_export"] = [
        "# redact and mask fields on export",
        NOW,
        "rule redact password",
        "rule mask api-key",
        "rule drop ua",
        log("2026-03-09T10:15:00Z", "auth", "alice@example.com", "level=info", "password=hunter2go",
            "api-key=K9XQ72LMZP41", "ua=curl/8.0", "ip=10.0.0.7", msg="login ok"),
        log("2026-03-09T11:00:00+0200", "web", "bob", "level=warn", "ip=10.0.0.9", "path=/admin",
            msg="slow response 912ms"),
        "export",
        "show #2",
        "rules",
    ]
    s["s2_report"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "bytes=120"),
        log("2026-03-09T10:05:00Z", "auth", "alice@example.com", "bytes=80", "level=error"),
        log("2026-03-09T10:07:00Z", "auth", "alice@example.com", "bytes=40"),
        log("2026-03-09T10:09:00Z", "auth", "alice@example.com"),
        log("2026-03-09T11:00:00Z", "web", "bob", "bytes=1500", "level=warn"),
        log("2026-03-09T11:30:00Z", "web", "bob"),
        log("2026-03-09T11:45:00Z", "web", "bob", "level=info"),
        log("2026-03-08T23:30:00-0200", "db", "carol@corp.test", "bytes=3"),
        log("2026-03-09T01:30:00+0100", "db", "carol@corp.test"),
        log("2026-03-10T08:00:00Z", "batch", "dave@example.com", "bytes=7", "level=debug"),
        "report",
        "days",
        "stats",
    ]
    s["s3_retention"] = [
        NOW,
        "retain 14",
        log("2026-02-01T09:00:00Z", "auth", "alice@example.com", msg="very old"),
        log("2026-03-08T09:00:00Z", "auth", "bob", msg="recent"),
        log("2026-02-10T09:00:00Z", "web", "carol@corp.test", msg="old"),
        log("2026-02-24T12:00:00Z", "web", "bob", msg="exactly fourteen days"),
        log("2026-03-12T09:00:00Z", "db", "erin", msg="dated after the clock"),
        log("2026-03-09T09:00:00Z", "auth", "bob", msg="recent again"),
        log("2026-03-09T10:00:00Z", "auth", "bob", msg="and again"),
        log("2026-03-09T11:00:00Z", "web", "bob", msg="web fresh"),
        "purge",
        "report",
        "export",
        "check",
    ]
    s["s4_alerts_scrub"] = [
        NOW,
        "window 60",
        "limit auth 2",
        "limit * 5",
        log("2026-03-10T10:00:00Z", "auth", "alice@example.com", msg="try 1 password=abcd1234"),
        log("2026-03-10T10:00:20Z", "auth", "alice@example.com", msg="try 2 token=zzzz9999 tok_AAAABBBB1234"),
        log("2026-03-10T10:00:40Z", "auth", "alice@example.com", msg="try 3"),
        log("2026-03-10T10:05:00Z", "web", "bob"),
        log("2026-03-10T10:05:10Z", "web", "bob"),
        "report",
        "export auth",
    ]
    s["s5_strict_keep"] = [
        NOW,
        "strict on",
        "rule keep level",
        "rule keep source",
        "rule mask session",
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "level=info", "session=abcdef123456",
            "ip=10.1.1.1", "source=web"),
        log("2026-03-09T10:01:00Z", "web", "bob", "level=error", "region=eu", "note=hello"),
        "export",
        "export keep=ip,note",
    ]
    return s


# ---------------------------------------------------------------- ref_tests
def ref_tests():
    t = {}
    t["t01_fields_sorted_folded"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "AUTH", "Alice@Example.com", "Level=INFO", "IP=10.0.0.1", "Zeta=1",
            "alpha=2", "bytes=10", msg="  padded message  "),
        log("2026-03-09T10:00:01Z", "web.eu_1", "bob", "k=1", "k=2"),
        log("2026-03-09T10:00:02Z", "web", "bob", "--", msg="after dashes"),
        log("2026-03-09T10:00:03Z", "web", "bob", "k=v", "--"),
        "log 2026-03-09T10:00:04Z web bob k=v -- one -- two",
        "log 2026-03-09T10:00:04Z web bob -- ",
        "export",
    ]
    t["t02_actions_and_salt"] = [
        NOW,
        "rule redact password",
        "rule drop ua",
        "rule pseudo ip",
        "rule mask card",
        "salt pepper and salt",
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "password=hunter2go", "ua=curl",
            "ip=10.0.0.7", "card=4111222233334444", "level=info"),
        log("2026-03-09T10:00:01Z", "auth", "bob", "ip=10.0.0.7", "card=555566667777"),
        "export",
        "salt other",
        "export auth",
    ]
    t["t03_precedence"] = [
        NOW,
        "rule mask session",
        "rule prefix sess",
        "rule redact sessionid",
        "rule pseudo sessionid",
        "rule drop token",
        "rule mask token",
        log("2026-03-09T10:00:00Z", "web", "bob", "session=abcdefghijkl", "sessionid=zzzzzzzzzzzz",
            "sessiontoken=qqqqqqqqqqqq", "token=wwwwwwwwwwww", "other=keep"),
        "export",
        "rules",
    ]
    t["t04_strict_keep"] = [
        NOW,
        "rule keep level",
        "rule keep ip",
        log("2026-03-09T10:00:00Z", "web", "bob", "level=info", "ip=10.0.0.1", "note=hello"),
        "export",
        "strict on",
        "export",
        "rule redact ip",
        "rule mask note",
        "rule keep note",
        "export",
        "strict off",
        "unrule ip",
        "unrule nothing",
        "export",
        "rules",
    ]
    t["t05_x_prefix_names"] = [
        NOW,
        "rule redact auth",
        "rule mask X-Session",
        log("2026-03-09T10:00:00Z", "web", "bob", "X-Auth=aaaa", "auth=bbbb", "AUTH=cccc",
            "x-session=abcdefgh1234", "session=abcdefgh1234", "x-trace=t1", "trace=t2"),
        "export",
        "rules",
        "unrule X-AUTH",
        "export",
    ]
    t["t06_message_scrub"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob", msg="user said password=abcdefgh and moved on"),
        log("2026-03-09T10:00:01Z", "web", "bob", msg="a secret=zzzzzzzz then tok_ABCDEFGH1234 end"),
        log("2026-03-09T10:00:02Z", "web", "bob", msg="tok_short tok_12345678 xtok_12345678abc apikey=KEYKEYKEYKEY1"),
        log("2026-03-09T10:00:03Z", "web", "bob", msg="no pair here: password= and token"),
        "export",
    ]
    long80 = "m" * 80
    t["t07_message_cut"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob", msg=long80),
        log("2026-03-09T10:00:01Z", "web", "bob", msg=long80 + "x"),
        log("2026-03-09T10:00:02Z", "web", "bob", msg="x" * 75 + " password=abcdefghijkl more words"),
        log("2026-03-09T10:00:03Z", "web", "bob", "k=v", msg="word " * 30),
        "export",
    ]
    t["t08_rejects"] = [
        NOW,
        "log 2026-13-09T10:00:00Z web bob",
        "log 2026-03-09T10:00:00 web bob k=v",
        "log 2026-03-09 web bob",
        "log 2026-03-09T10:00:00Z web",
        "log 2026-03-09T10:00:00+2460 web bob",
        "log 2026-03-09T10:00:00Z we$b bob",
        "log 2026-03-09T10:00:00Z web bob novalue",
        "log 2026-03-09T10:00:00Z web bob =novalue",
        "log 2026-03-09T10:00:00Z web bob bytes=12x",
        "log 2026-03-09T10:00:00Z web bob bytes=-5",
        "log 2026-03-09T10:00:00Z web bob bytes=1_0",
        "log 2026-03-09T10:00:00Z web bob bytes=",
        "log",
        "report",
    ]
    t["t09_offsets_and_days"] = [
        NOW,
        log("2026-03-09T23:30:00-0200", "web", "bob", msg="negative whole hours"),
        log("2026-03-09T00:30:00+0100", "web", "bob", msg="positive crossing back"),
        log("2026-03-09T12:00:00+0530", "web", "bob", msg="half hour"),
        log("2026-03-09T12:00:00-0330", "web", "bob", msg="negative half hour"),
        log("2026-03-09T12:00:00+0000", "web", "bob", msg="zero offset"),
        log("2026-03-09T23:59:59", "web", "bob", msg="no zone"),
        log("2026-03-01T00:00:00+1400", "web", "bob", msg="month edge"),
        "days",
        "export",
    ]
    t["t10_retention_bounds"] = [
        NOW,
        "retain 10",
        log("2026-02-28T12:00:00Z", "web", "bob", msg="exactly ten days"),
        log("2026-02-28T11:59:59Z", "web", "bob", msg="one second over"),
        log("2026-03-10T12:00:01Z", "web", "bob", msg="one second ahead"),
        log("2026-03-01T12:00:00Z", "web", "carol@corp.test", msg="nine days"),
        "purge",
        "purge",
        "retain 0",
        "now 2026-03-10T12:00:01Z",
        "purge",
        "export",
    ]
    t["t11_purge_isolated"] = [
        NOW,
        "retain 20",
        log("2026-01-01T12:00:00Z", "a", "u1", msg="old 1"),
        log("2026-03-01T12:00:00Z", "a", "u1", msg="fresh 2"),
        log("2026-01-02T12:00:00Z", "b", "u2", msg="old 3"),
        log("2026-03-02T12:00:00Z", "b", "u2", msg="fresh 4"),
        log("2026-01-03T12:00:00Z", "c", "u3", msg="old 5"),
        "purge",
        "days",
        log("2026-01-04T12:00:00Z", "c", "u3", msg="old again"),
        "purge",
        "show 6",
        "show 7",
    ]
    t["t12_windows"] = [
        NOW,
        "window 60",
        "limit * 2",
        log("2026-03-10T10:00:00Z", "a", "u"),
        log("2026-03-10T10:01:00Z", "a", "u"),
        log("2026-03-10T10:02:00Z", "a", "u"),
        log("2026-03-10T10:00:00Z", "b", "u"),
        log("2026-03-10T10:00:59Z", "b", "u"),
        log("2026-03-10T10:00:30Z", "c", "u"),
        log("2026-03-10T10:00:31Z", "c", "u"),
        log("2026-03-10T10:00:32Z", "c", "u"),
        log("2026-03-10T10:00:33Z", "c", "u"),
    ] + [log("2026-03-10T10:01:31Z", "d", "u")] * 5 + [
        "report",
        "window 61",
        "report",
        "window 0",
        "window 1",
        "report",
    ]
    t["t13_future_days"] = [
        NOW,
        log("2026-03-10T12:00:01Z", "a", "u", msg="one second"),
        log("2026-03-11T12:00:00Z", "a", "u", msg="exactly a day"),
        log("2026-03-11T12:00:01Z", "a", "u", msg="a day and a second"),
        log("2026-03-13T11:00:00Z", "a", "u", msg="almost three days"),
        log("2026-03-10T12:00:00Z", "a", "u", msg="now"),
        log("2026-03-10T11:59:59Z", "a", "u", msg="past"),
        "report",
        "now 2026-03-12T12:00:00Z",
        "report",
    ]
    t["t14_average_even"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "a", "u1"),
        log("2026-03-09T10:00:01Z", "a", "u1"),
        log("2026-03-09T10:00:02Z", "a", "u1"),
        log("2026-03-09T10:00:03Z", "b", "u1"),
        log("2026-03-09T10:00:04Z", "b", "u1"),
        "report",
        log("2026-03-09T10:00:05Z", "a", "u1"),
        log("2026-03-09T10:00:06Z", "b", "u1"),
        "report",
        log("2026-03-09T10:00:07Z", "a", "u1"),
        log("2026-03-09T10:00:08Z", "b", "u1"),
        "report",
        log("2026-03-09T10:00:09Z", "a", "u1"),
        "report",
        log("2026-03-09T10:00:10Z", "c", "u1"),
        "report",
    ]
    t["t15_top_users"] = [
        NOW,
        "top 2",
        log("2026-03-09T10:00:00Z", "a", "alpha"),
        log("2026-03-09T10:00:01Z", "a", "alpha"),
        log("2026-03-09T10:00:02Z", "a", "alpha"),
        log("2026-03-09T10:00:03Z", "a", "beta"),
        log("2026-03-09T10:00:04Z", "a", "beta"),
        log("2026-03-09T10:00:05Z", "a", "gamma"),
        "report",
        "top 5",
        "report",
        "top 0",
        "top x",
    ]
    t["t16_levels"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "a", "u", "level=debug"),
        log("2026-03-09T10:00:01Z", "a", "u", "level=ERROR"),
        log("2026-03-09T10:00:02Z", "a", "u"),
        log("2026-03-09T10:00:03Z", "a", "u", "level=fatal"),
        log("2026-03-09T10:00:04Z", "a", "u", "level=warn"),
        log("2026-03-09T10:00:05Z", "a", "u", "level=error"),
        log("2026-03-09T10:00:06Z", "a", "u", "level=info"),
        log("2026-03-09T10:00:07Z", "a", "u", "level=audit"),
        "report",
    ]
    t["t17_domains"] = [NOW] + [
        log("2026-03-09T10:%02d:%02dZ" % (i, j), "a", user)
        for i, (user, n) in enumerate([("a@b@c.org", 5), ("bob@", 4), ("plain", 3), ("@x.net", 2), ("z@c.org", 1)])
        for j in range(n)
    ] + ["top 5", "report"]
    t["t18_show_ids"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "a", "u", "k=1"),
        log("2026-03-09T10:00:01Z", "a", "u", "k=2"),
        log("2026-03-09T10:00:02Z", "a", "u", "k=3"),
        "show 2",
        "show #3",
        "show ##1",
        "show 4",
        "show 0",
        "show #",
        "show x1",
        "show",
        "show 1 2",
        "show 007",
    ]
    t["t19_empty_store"] = [
        "report",
        "days",
        "stats",
        "export",
        "export web",
        "purge",
        "rules",
        "check",
        "unrule zed",
    ]
    t["t20_stats_names"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "a", "u", "x-trace=1", "trace=2", "level=info", "zone=1", "alpha=1"),
        log("2026-03-09T10:00:01Z", "a", "u", "Trace=3", "level=warn", "level=error", "zone=2"),
        log("2026-03-09T10:00:02Z", "a", "u", "trace=4", "level=debug"),
        log("2026-03-09T10:00:03Z", "a", "u", "x-trace=4"),
        "stats",
        "export",
    ]
    t["t21_bytes_and_largest"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "a", "u", "bytes=10"),
        log("2026-03-09T10:00:01Z", "a", "u", "bytes="),
        log("2026-03-09T10:00:02Z", "a", "u", "bytes=10"),
        log("2026-03-09T10:00:03Z", "a", "u"),
        log("2026-03-09T10:00:04Z", "a", "u", "bytes=0010"),
        log("2026-03-09T10:00:05Z", "a", "u", "bytes=12345678901234567890"),
        "report",
        "days",
    ]
    t["t22_usage_errors"] = [
        NOW,
        "now",
        "now yesterday",
        "now 2026-03-10T12:00:00Z extra",
        "retain",
        "retain -3",
        "retain 3.5",
        "retain 5",
        "window 0",
        "limit",
        "limit a",
        "limit a b",
        "limit A 3",
        "limit * 7",
        "top",
        "salt",
        "strict maybe",
        "strict on",
        "rule",
        "rule redact",
        "rule shred x",
        "rule redact a b",
        "rule redact x-",
        "rule prefix",
        "rule prefix a b c d",
        "rule prefix a shred",
        "rule prefix a keep",
        "rule prefix A mask",
        "unrule",
        "unrule a b",
        "export a b",
        "frobnicate",
        "help",
        "# comment",
        "",
        "   ",
        "check",
    ]
    t["t23_export_filter_keep_once"] = [
        NOW,
        "strict on",
        "rule keep level",
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "level=info", "ip=10.0.0.1", "note=n1"),
        log("2026-03-09T10:00:01Z", "web", "bob", "level=warn", "ip=10.0.0.2", "note=n2"),
        "export WEB",
        "export nosuch",
        "export keep=",
        "export auth keep=ip,,NOTE",
    ]
    t["t24_unrule_prefix"] = [
        NOW,
        "rule prefix tmp drop",
        "rule redact tmp",
        log("2026-03-09T10:00:00Z", "a", "u", "tmp=1", "tmpx=2", "other=3"),
        "export",
        "unrule tmp",
        "export",
        "rules",
        "unrule tmp",
    ]
    for i in range(1, 4):
        t["t%d_generated_ordinary_%d" % (24 + i, i)] = ordinary_session(i)
    return t


# ---------------------------------------------------------------- ref_edge
def ref_edge():
    e = {}
    # M01 -- a value may contain = (padding, query text)
    e["e01_equals_in_values"] = [
        NOW,
        "rule redact secret",
        "rule mask session",
        "rule drop cursor",
        log("2026-03-09T10:00:00Z", "web", "alice@example.com", "secret=YWJjZGVm==", "session=abc=def12345",
            "note=a=b=c", "cursor=x=1", "level=info"),
        log("2026-03-09T10:00:01Z", "web", "bob", "secret===", "session=a=", "note==x"),
        "export",
        "stats",
    ]
    e["e02_equals_strict_keep"] = [
        NOW,
        "strict on",
        "rule keep level",
        "rule keep x-trace",
        "rule keep path",
        log("2026-03-09T10:00:00Z", "web", "bob", "x-trace=a=b", "level=info", "zz=c=d", "path=/p?q=1&r=2"),
        "export",
        "show 1",
    ]
    # M02 -- only the exact x- prefix is ignored
    e["e03_prefix_strict_keep"] = [
        NOW,
        "strict on",
        "rule keep id",
        "rule keep level",
        log("2026-03-09T10:00:00Z", "web", "bob", "xid=77", "x-id=88", "id=99", "level=info", "x-level=warn"),
        log("2026-03-09T10:00:01Z", "web", "bob", "xxid=1", "-id=2", "x-xid=3", "-x-id=4"),
        "export",
        "stats",
    ]
    e["e04_prefix_rule_names"] = [
        NOW,
        "rule prefix xfer",
        "rule redact xray",
        log("2026-03-09T10:00:00Z", "web", "bob", "xfer_id=1", "x-ferry=2", "fer_b=3", "xfers=4", "ray=5",
            "xray=6", "x-xray=7", "x-x-ray=8"),
        "export",
        "stats",
        "rules",
        "unrule xray",
        "export",
    ]
    # M03 -- a partial mask of a value shorter than four characters
    e["e05_mask_lengths"] = [
        NOW,
        "rule mask a",
        "rule mask b",
        "rule mask c",
        "rule mask d",
        "rule mask e",
        "rule mask f",
        "rule mask g",
        "rule mask h",
        log("2026-03-09T10:00:00Z", "web", "bob", "a=", "b=x", "c=xy", "d=xyz", "e=wxyz", "f=abcdefg",
            "g=abcdefgh", "h=abcdefghijklmnopqrstu"),
        "export",
    ]
    e["e06_mask_short_in_message"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob", msg="login password=ab token=xyz other words"),
        log("2026-03-09T10:00:01Z", "web", "bob", msg="pin secret=7 and apikey=abcd"),
        "export",
    ]
    # M04 -- every occurrence, any letter case
    e["e07_scrub_many_occurrences"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob",
            msg="password=aaaaaaaa password=bbbbbbbb password=cccccccc token=dddddddd secret=eeeeeeee"),
        log("2026-03-09T10:00:01Z", "web", "bob", msg="token=1111 token=2222 token=3333"),
        "export",
    ]
    e["e08_scrub_letter_case"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob", msg="Password=abcdefgh SECRET=ijklmnop Token=qrstuvwx"),
        log("2026-03-09T10:00:01Z", "web", "bob", msg="ApiKey=abcdefghijkl and PASSWD=zxcvbnmasd"),
        "export",
    ]
    # M05 -- every prefix rule applies
    e["e09_two_prefix_rules"] = [
        NOW,
        "rule prefix auth_ drop",
        "rule prefix cred mask",
        log("2026-03-09T10:00:00Z", "web", "bob", "auth_user=alice", "auth_pw=hunter2go", "cred_id=abcdefghij",
            "other=keep"),
        "export",
        "rules",
    ]
    e["e10_three_prefix_rules"] = [
        NOW,
        "rule prefix tmp_ redact",
        "rule prefix dbg drop",
        "rule prefix usr mask",
        "rule mask dbg_level",
        "rule pseudo usr_name",
        "salt s1",
        log("2026-03-09T10:00:00Z", "web", "bob", "tmp_a=1", "dbg_x=2", "dbg_level=verbose", "usr_name=alice",
            "usr_mail=alice@example.com", "keep=3"),
        "export",
    ]
    # M06 -- a limit of 0 is a limit
    e["e11_limit_zero"] = [
        NOW,
        "limit auth 0",
        "limit * 5",
        log("2026-03-10T10:00:00Z", "auth", "alice@example.com"),
        log("2026-03-10T10:00:00Z", "web", "bob"),
        log("2026-03-10T10:00:10Z", "web", "bob"),
        "report",
    ]
    e["e12_limit_zero_and_equal"] = [
        NOW,
        "window 120",
        "limit * 3",
        "limit web 0",
        "limit mail 2",
        "limit db 0",
        log("2026-03-10T10:00:00Z", "web", "u1"),
        log("2026-03-10T10:00:05Z", "web", "u1"),
        log("2026-03-10T10:00:00Z", "mail", "u2"),
        log("2026-03-10T10:00:30Z", "mail", "u2"),
        log("2026-03-10T10:00:00Z", "api", "u3"),
        "limit * 4",
        "report",
    ]
    # M07 -- purge removes every old record
    e["e13_purge_run_of_old"] = [
        NOW,
        "retain 10",
        log("2026-01-01T10:00:00Z", "web", "u1", msg="old 1"),
        log("2026-01-02T10:00:00Z", "web", "u1", msg="old 2"),
        log("2026-01-03T10:00:00Z", "web", "u1", msg="old 3"),
        log("2026-01-04T10:00:00Z", "web", "u1", msg="old 4"),
        log("2026-01-05T10:00:00Z", "web", "u1", msg="old 5"),
        log("2026-03-09T10:00:00Z", "web", "u1", msg="fresh 6"),
        "purge",
        "report",
        "export",
    ]
    e["e14_purge_after_clock_moves"] = [
        NOW,
        "retain 5",
        log("2026-03-01T10:00:00Z", "a", "u", msg="one"),
        log("2026-03-02T10:00:00Z", "a", "u", msg="two"),
        log("2026-03-08T10:00:00Z", "b", "u", msg="three"),
        log("2026-03-09T10:00:00Z", "b", "u", msg="four"),
        "purge",
        "now 2026-03-20T00:00:00Z",
        "purge",
        "report",
        "export",
    ]
    # M08 -- export keep= is for that export only
    e["e15_keep_for_one_export"] = [
        NOW,
        "strict on",
        "rule keep level",
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "level=info", "ip=10.0.0.1", "note=n1"),
        "export keep=ip,note",
        "export",
        "rules",
    ]
    e["e16_keep_repeated"] = [
        NOW,
        "strict on",
        log("2026-03-09T10:00:00Z", "auth", "alice@example.com", "level=info", "ip=10.0.0.1", "note=n1"),
        log("2026-03-09T10:00:01Z", "web", "bob", "level=warn", "ip=10.0.0.2", "note=n2"),
        "export auth keep=ip",
        "export web keep=note",
        "export",
        "show 1",
        "rules",
    ]
    # M09 -- shares round halves up
    e["e17_share_sixteenths"] = [NOW] + [
        log("2026-03-09T10:%02d:00Z" % i, src, user)
        for i, (src, user) in enumerate([
            ("a", "u1"), ("b", "u2"), ("c", "u3"), ("d", "u4"), ("e", "u5"),
            ("a", "u1"), ("a", "u1"), ("a", "u1"),
            ("e", "u2"), ("e", "u2"), ("e", "u2"), ("e", "u2"),
            ("f", "u9"), ("f", "u9"), ("f", "u9"), ("f", "u9")])
    ] + ["report", "stats"]
    lines = [NOW]
    for i in range(80):
        src = "s%d" % (0 if i == 0 else (1 if i < 4 else 2 + i % 3))
        lines.append(log("2026-03-09T10:%02d:%02dZ" % (i // 60, i % 60), src, "u%d" % (0 if i < 1 else (1 + i % 2)),
                         "level=%s" % ("error" if i == 5 else "info")))
    e["e18_share_eightieths"] = lines + ["report", "stats"]
    # M10 -- equal counts are listed in name order
    e["e19_rank_ties_sources"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "u1"),
        log("2026-03-09T10:00:01Z", "db", "u1"),
        log("2026-03-09T10:00:02Z", "auth", "u1"),
        log("2026-03-09T10:00:03Z", "mail", "u1"),
        log("2026-03-09T10:00:04Z", "batch", "u1"),
        log("2026-03-09T10:00:05Z", "web", "u1"),
        log("2026-03-09T10:00:06Z", "db", "u1"),
        log("2026-03-09T10:00:07Z", "auth", "u1"),
        "report",
    ]
    e["e20_rank_ties_users_domains"] = [
        NOW,
        "top 4",
        log("2026-03-09T10:00:00Z", "a", "zed@z.org", "k=1", "j=2"),
        log("2026-03-09T10:00:01Z", "a", "amy@a.org", "k=1"),
        log("2026-03-09T10:00:02Z", "a", "mia@m.org", "j=1"),
        log("2026-03-09T10:00:03Z", "a", "bob", "j=1"),
        log("2026-03-09T10:00:04Z", "a", "zed@z.org"),
        log("2026-03-09T10:00:05Z", "a", "amy@a.org"),
        "report",
        "stats",
    ]
    # interactions: several slips change one output together
    e["e21_interplay_fields"] = [
        NOW,
        "strict on",
        "rule keep level",
        "rule keep x-trace",
        "rule prefix xfer drop",
        "rule prefix tok mask",
        "rule mask cookie",
        log("2026-03-09T10:00:00Z", "web", "alice@example.com", "x-trace=a=b==", "xfer_id=1", "tok_a=abcdefgh==",
            "tokb=xy", "cookie=ab=", "level=info", "xlevel=warn"),
        "export",
        "stats",
        "report",
    ]
    e["e22_interplay_message"] = [
        NOW,
        log("2026-03-09T10:00:00Z", "web", "bob",
            msg="Password=ab password=abcdefgh token=xyz SECRET=abcdefghijkl tok_ABCDEFGH1234 secret=q"),
        log("2026-03-09T10:00:01Z", "api", "bob", "x-note=a=b", msg="apikey=abc apikey=abcd apikey=abcde apikey=abcdefghij"),
        "export",
    ]
    tab = [NOW, "retain 7", "limit * 2", "limit web 0", "window 30"]
    for i in range(16):
        tab.append(log("2026-03-%02dT10:%02d:00Z" % (3 if i < 6 else 9, i), ["web", "db", "auth", "mail"][i % 4],
                       ["bob", "amy@a.org", "zed@z.org", "mia@a.org"][i % 4]))
    tab += ["purge", "report", "stats", "export keep=ip", "export", "rules"]
    e["e23_interplay_report"] = tab
    e["e24_interplay_policy"] = [
        NOW,
        "strict on",
        "rule keep level",
        "rule prefix s_ mask",
        "rule prefix t_ redact",
        "rule keep xid",
        log("2026-03-09T10:00:00Z", "web", "bob", "s_a=abcdefgh", "t_b=zz=z", "xid=1", "level=info"),
        "export keep=s_a,xid",
        "export",
        "unrule s_",
        "export",
        "rules",
    ]
    e["e25_generated_hazards_a"] = hazard_session(21)
    e["e26_generated_hazards_b"] = hazard_session(22)
    e["e27_generated_hazards_c"] = hazard_session(23, 0.5)
    return e


def main():
    smoke_dir = os.path.join(TASK, "public", "smoke")
    for name, lines in smoke().items():
        write(smoke_dir, name, lines)
    for name, lines in ref_tests().items():
        write(os.path.join(HERE, "ref_tests"), name, lines)
    for name, lines in ref_edge().items():
        write(os.path.join(HERE, "ref_edge"), name, lines)
    print("inputs written")


if __name__ == "__main__":
    main()
