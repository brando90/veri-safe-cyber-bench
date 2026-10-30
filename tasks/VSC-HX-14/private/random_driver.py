#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Rarity measurement: how many random sessions does a quick driver need to hit each defect?

usage: python3 random_driver.py [--cap N] [--seed S] [tree ...]

For the gold tree and every mutant it runs random sessions in-process (same
loop as main.py: parse, dispatch, full_check) and counts how many sessions
pass before the first failure (INVARIANT or any other exception).  Two
generators:

  ordinary  an independent, README-driven generator: uniform dates 2000-2030,
            any minute of the day, offsets that are multiples of 15 minutes in
            the allowed range, durations from a handful of forms, plain titles
            (single blanks), ids from a small name pool, random rules.
  targeted  Gen from make_inputs.py with exactly the hazard of that defect.

Each session has 40 commands for ordinary and about 150 for targeted.  The
gold tree must never fail.  Prints a table (sessions needed, or '>cap').
"""
import argparse
import importlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

HAZARD_OF = {"M01": "civil", "M02": "cats", "M03": "varint", "M04": "offset", "M05": "weekly",
             "M06": "snap", "M07": "natural", "M08": "ref", "M09": "move", "M10": "title"}

WORDS = ["alpha", "beta", "gamma", "delta", "standup", "review", "sync", "lunch", "demo", "retro"]
WD = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


def naive_session(rng, n=40):
    lines = []
    names = []

    def date(lo=2000, hi=2030):
        y = rng.randint(lo, hi)
        m = rng.randint(1, 12)
        d = rng.randint(1, 28 if m == 2 else 30)
        return "%04d-%02d-%02d" % (y, m, d)

    def start():
        s = "%sT%02d:%02d" % (date(), rng.randint(0, 23), rng.randint(0, 59))
        if rng.random() < 0.2:
            s += ":%02d" % rng.randint(0, 59)
        return s

    def tz():
        minutes = rng.randrange(-12 * 60, 14 * 60 + 1, 15)
        if minutes == 0:
            return "Z"
        sign = "-" if minutes < 0 else "+"
        h, m = divmod(abs(minutes), 60)
        form = rng.choice(["colon", "colon", "plain"])
        if m == 0 and rng.random() < 0.3:
            return "%s%02d" % (sign, h)
        return "%s%02d:%02d" % (sign, h, m) if form == "colon" else "%s%02d%02d" % (sign, h, m)

    def dur():
        kind = rng.randint(0, 2)
        if kind == 0:
            return "%dm" % rng.choice([15, 30, 45, 60, 90, 120])
        if kind == 1:
            return "%dh%dm" % (rng.randint(0, 5), rng.randrange(0, 60, 5))
        return "%.2fh" % rng.uniform(0.25, 6)

    def title():
        return " ".join(rng.choice(WORDS) for _ in range(rng.randint(1, 3)))

    def rule(day_text):
        kind = rng.choice(["daily", "weekly", "monthly", "yearly"])
        parts = [kind]
        if rng.random() < 0.4:
            parts.append("every=%d" % rng.randint(2, 4))
        if kind == "weekly" and rng.random() < 0.6:
            parts.append("on=" + ",".join(sorted(set(rng.choice(WD) for _ in range(rng.randint(1, 3))),
                                                key=WD.index)))
        if kind == "monthly" and rng.random() < 0.5:
            parts.append("monthday=%d" % rng.randint(1, 31))
        if rng.random() < 0.5:
            parts.append("count=%d" % rng.randint(2, 12))
        return ";".join(parts)

    def cats():
        return ",".join(rng.sample(["work", "team", "ops", "home", "gym"], rng.randint(1, 3)))

    for _ in range(n):
        roll = rng.random()
        if roll < 0.35 or not names:
            name = rng.choice(["a", "b", "c", "mtg", "x1", "x2", "ev", "room"]) + str(rng.randint(1, 30))
            st = start()
            opts = []
            if rng.random() < 0.8:
                opts.append("dur=" + dur())
            if rng.random() < 0.6:
                opts.append("rule=" + rule(st))
            if rng.random() < 0.6:
                opts.append("tz=" + tz())
            if rng.random() < 0.5:
                opts.append("prio=%d" % rng.randint(0, 9))
            if rng.random() < 0.4:
                opts.append("cat=" + cats())
            lines.append('event add %s "%s" %s %s' % (name, title(), st, " ".join(opts)))
            names.append(name)
            continue
        e = rng.choice(names)
        d0 = date()
        d1 = date()
        lo, hi = sorted([d0, d1])
        if roll < 0.42:
            lines.append("event show " + e)
        elif roll < 0.52:
            lines.append("expand %s %s %s" % (e, d0, d0[:4] + "-12-31"))
        elif roll < 0.60:
            lines.append("agenda %s %s" % (d0, d0[:8] + "28"))
        elif roll < 0.64:
            lines.append("busy %s %s" % (d0, d0[:8] + "28"))
        elif roll < 0.72:
            lines.append("skip %s %s" % (e, d0))
        elif roll < 0.78:
            lines.append("event move %s %s" % (e, start()))
        elif roll < 0.82:
            lines.append("event rule %s %s" % (e, rule(d0)))
        elif roll < 0.85:
            lines.append('event retitle %s "%s"' % (e, title()))
        elif roll < 0.88:
            lines.append("event set %s tz=%s" % (e, tz()))
        elif roll < 0.90:
            lines.append("event cat %s %s" % (e, cats()))
        elif roll < 0.92:
            lines.append("export text")
        elif roll < 0.94:
            lines.append("export pack")
        elif roll < 0.96:
            lines.append("shift %s %d %s" % (d0, rng.randint(-30, 30), rng.choice(["days", "months", "years"])))
        elif roll < 0.98:
            lines.append(rng.choice(["offset " + tz(), "dur " + dur(), "snap " + start(),
                                     "date %d" % rng.randint(0, 30000),
                                     "ordinal " + d0, "ref %d" % rng.randint(0, 100000)]))
        else:
            lines.append("check")
    return lines


def child(tree, gen, hazard, cap, seed, nlines):
    """Run in a fresh interpreter with TREE on sys.path.  Prints a JSON result."""
    sys.path.insert(0, tree)
    sys.dont_write_bytecode = True
    import invariant
    import lexer
    from errors import CommandError, InvariantViolation
    from world import World

    class Null:
        def emit(self, line):
            pass

        def flush(self):
            pass

    def run(lines):
        w = World(Null())
        for line in lines:
            try:
                cmd = lexer.parse(line)
                if cmd is None:
                    continue
                w.dispatch(cmd)
                invariant.full_check(w)
            except CommandError:
                pass
            except InvariantViolation as exc:
                return "INVARIANT: %s" % exc
            except Exception as exc:  # a traceback in the real program
                return "Traceback: %r" % (exc,)
        return None

    rng = random.Random(seed)
    cmds = 0
    pre = json.load(open(hazard)) if gen == "targeted" else None
    for i in range(1, cap + 1):
        if gen == "ordinary":
            lines = naive_session(rng, nlines)
        else:
            if i > len(pre):
                break
            lines = pre[i - 1]
        cmds += len(lines)
        why = run(lines)
        if why:
            print(json.dumps({"sessions": i, "commands": cmds, "why": why[:90]}))
            return
    print(json.dumps({"sessions": None, "commands": cmds, "why": ""}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--gen", nargs=4, metavar=("HAZARD", "COUNT", "N", "OUT"))
    ap.add_argument("--child", nargs=4, metavar=("TREE", "GEN", "HAZARD", "N"))
    ap.add_argument("trees", nargs="*")
    args = ap.parse_args()
    if args.gen:
        hazard, count, nlines, out = args.gen
        sys.path.insert(0, HERE)
        import make_inputs  # gold tree only: steers the generator
        r = random.Random(args.seed)
        sess = [make_inputs.Gen(r.randrange(10 ** 9), (hazard,), max_events=40).session(int(nlines))
                for _ in range(int(count))]
        json.dump(sess, open(out, "w"))
        return
    if args.child:
        tree, gen, hazard, nlines = args.child
        child(tree, gen, hazard, args.cap, args.seed, int(nlines))
        return
    trees = [("gold", os.path.join(HERE, "gold"))]
    for m in sorted(os.listdir(os.path.join(HERE, "mutants"))):
        trees.append((m, os.path.join(HERE, "mutants", m)))
    if args.trees:
        trees = [t for t in trees if any(t[0].startswith(x) for x in args.trees)]
    print("| Tree | ordinary: sessions to first failure | targeted: sessions to first failure |")
    print("|---|---|---|")
    tmp = os.environ.get("TMPDIR", "/tmp")
    pre = {}
    for h in sorted(set(HAZARD_OF.values())):
        pre[h] = os.path.join(tmp, "rd_%s.json" % h)
        subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--seed", str(args.seed),
                        "--gen", h, str(max(50, args.cap // 10)), "150", pre[h]], check=True,
                       env={"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0",
                            "LC_ALL": "C.UTF-8"})
    pre[""] = pre["civil"]
    for name, tree in trees:
        cells = []
        for gen, n in (("ordinary", 40), ("targeted", 150)):
            hazard = pre[HAZARD_OF.get(name[:3], "")] if gen == "targeted" else ""
            cap = args.cap if gen == "ordinary" else max(50, args.cap // 10)
            res = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--cap", str(cap),
                                  "--seed", str(args.seed), "--child", tree, gen, hazard, str(n)],
                                 capture_output=True, text=True,
                                 env={"PYTHONPATH": "", "PATH": os.environ.get("PATH", ""),
                                      "PYTHONHASHSEED": "0", "LC_ALL": "C.UTF-8"})
            try:
                data = json.loads(res.stdout.strip().splitlines()[-1])
            except Exception:
                cells.append("driver error: " + (res.stderr.strip().splitlines() or ["?"])[-1])
                continue
            if data["sessions"] is None:
                cells.append(">%d sessions (%d commands), none" % (cap, data["commands"]))
            else:
                cells.append("%d sessions (%d commands)" % (data["sessions"], data["commands"]))
        print("| %s | %s | %s |" % (name, cells[0], cells[1]))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
