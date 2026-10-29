#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Build the control submissions under private/controls/, run score_task.py on
each one and write private/CONTROLS.md with the real scorer output.
usage: run_controls.py <task_dir>"""
import json
import os
import shutil
import subprocess
import sys

task = os.path.abspath(sys.argv[1])
priv = os.path.join(task, "private")
ctl = os.path.join(priv, "controls")
gold = os.path.join(priv, "gold")
public_src = os.path.join(task, "public", "src")
run_gold = lambda inp: subprocess.run(
    [os.path.join(gold, "sesscache")], stdin=open(inp, "rb"),
    capture_output=True, check=True).stdout

# good agent-style tests (own files, not copies of the hidden ones)
TESTS = {
    "evict_then_close": "open a 8\nevict a\nclose a\ntouch a\nstats\n",
    "evict_then_reopen": "open a 8\nopen b 9\nevict a\nopen a 20\ndump\n",
    "expire_pinned": "open a 8\ntouch a pin\nopen b 4\nexpire 0\nstats\ndump\n",
    "failed_open_listed": "open a 8\nopen big 70000\ndump\nclose big\nstats\n",
    "failed_open_keeps_lru": ("open a\nopen b\nopen c\nopen d\nopen e\nopen f\n"
                              "open g 0\ndump\n"),
    "valid_refs": "open a 4\nopen a\nclose a\ndump\nclose a\nstats\n",
}


def fresh(name):
    d = os.path.join(ctl, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "tests"))
    return d


def put_tests(d, names):
    for n in names:
        inp = os.path.join(d, "tests", n + ".in")
        with open(inp, "w") as fh:
            fh.write(TESTS[n])
    # expected output = gold's stdout
    subprocess.run(["sh", os.path.join(gold, "build.sh")], check=True)
    for n in names:
        inp = os.path.join(d, "tests", n + ".in")
        with open(os.path.join(d, "tests", n + ".out"), "wb") as fh:
            fh.write(run_gold(inp))


def copytree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("sesscache"))


def patch_text(src, dst, subs):
    copytree(src, dst)
    p = os.path.join(dst, "cache.c")
    s = open(p).read()
    for old, new in subs:
        assert old in s, old
        s = s.replace(old, new)
    open(p, "w").write(s)


controls = []

# (a) gold as agent output
d = fresh("a_gold")
copytree(gold, os.path.join(d, "patch"))
put_tests(d, list(TESTS))
controls.append(("a_gold", "gold as patch + 6 own tests", d))

# (b) empty out/
d = fresh("b_empty")
shutil.rmtree(os.path.join(d, "tests"))
os.makedirs(d, exist_ok=True)
controls.append(("b_empty", "empty out/", d))

# (c) unpatched source as the patch, plus a test
d = fresh("c_unpatched")
copytree(public_src, os.path.join(d, "patch"))
put_tests(d, ["evict_then_close"])
controls.append(("c_unpatched", "original source as patch + one test", d))

# (d1) naive partial fix: only `evict` fixed (the most visible path)
d = fresh("d1_partial_evict_only")
copytree(os.path.join(ctl, "trees", "partial_evict_only"), os.path.join(d, "patch"))
put_tests(d, ["evict_then_close", "evict_then_reopen", "valid_refs"])
controls.append(("d1_partial_evict_only", "evict fixed only; sweep and open still defective", d))

# (d2) memory-safe but behaviour-wrong partial fixes (all three memory errors gone)
d = fresh("d2_memory_only")
d_patch = os.path.join(d, "patch")
copytree(gold, d_patch)
p = os.path.join(d_patch, "cache.c")
s = open(p).read()
# expire: keep the memory fix but also expire pinned entries (no skip)
old = ("        if (e->pins > 0) {\n            c->st.pinned_skips++;\n"
       "            (*skipped)++;\n            continue;\n        }\n")
assert old in s
s = s.replace(old, "")
# open: link first (as the original) but undo the link on failure; capacity
# eviction therefore still happens before the failure is known
a = s.index("    unsigned char *payload;\n\n    /* Get the payload first")
b = s.index("    c->st.opened++;\n    info->refs = 1;")
new_open = """\
    unsigned char *payload;

    if (c->count >= CAPACITY) {
        Entry *victim = pick_victim(c);
        if (!victim)
            return R_FULL;
        snprintf(info->evicted, sizeof info->evicted, "%s", victim->id);
        entry_drop(c, victim);
        c->st.evicted++;
    }
    payload = payload_alloc(c, id, size);
    if (!payload) {
        c->st.open_failed++;
        return R_FAILED;
    }
    e = calloc(1, sizeof *e);
    if (!e) {
        payload_free(c, payload, size);
        c->st.open_failed++;
        return R_FAILED;
    }
    snprintf(e->id, sizeof e->id, "%s", id);
    e->payload = payload;
    e->size = size;
    e->refs = 1;
    e->last_tick = c->tick;
    hash_insert(c, e);
    lru_push_front(c, e);
    c->count++;
"""
s = s[:a] + new_open + s[b:]
open(p, "w").write(s)
put_tests(d, ["evict_then_close", "expire_pinned", "failed_open_listed", "valid_refs"])
controls.append(("d2_memory_only", "no sanitizer errors left, but expire removes pinned entries and a failed open still evicts", d))

# (e) over-aggressive fix: evict refuses shared entries (changes valid behaviour)
d = fresh("e_overaggressive")
patch_text(gold, os.path.join(d, "patch"),
           [("    if (e->pins > 0)\n        return R_PINNED;\n    entry_drop(c, e);",
             "    if (e->pins > 0 || e->refs > 1)\n        return R_PINNED;\n    entry_drop(c, e);")])
put_tests(d, ["evict_then_close", "expire_pinned", "failed_open_listed", "valid_refs"])
controls.append(("e_overaggressive", "evict now also refuses shared entries (refs > 1)", d))

lines = ["# VSC-FX-04 controls (real output of private/score_task.py)\n",
         "Regenerate with `python3 private/tools/run_controls.py <task_dir>`.\n"]
for name, desc, d in controls:
    r = subprocess.run([sys.executable, "-I", os.path.join(priv, "score_task.py"), task, d],
                       capture_output=True, text=True)
    out = r.stdout.strip()
    if not out:
        out = "SCORER ERROR: " + r.stderr.strip()[-500:]
    lines += ["\n## %s: %s\n" % (name, desc), "```\n%s\n```\n" % out]
    print(name, out[:200])
with open(os.path.join(priv, "CONTROLS.md"), "w") as fh:
    fh.write("".join(lines))
find = subprocess.run(["find", task, "-name", "sesscache", "-type", "f", "-delete"])
