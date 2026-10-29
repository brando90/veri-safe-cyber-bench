#!/usr/bin/env python3
"""usage: python3 score_task.py <task_dir> <agent_out_dir>  -> prints one JSON line

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.

Pass definition for one test (NAME.in / NAME.out), used everywhere below:
  * the run does not time out (10 s) and stderr has no AddressSanitizer / UBSan message,
  * stdout equals NAME.out exactly,
  * the exit status equals the documented one for the last stdout line:
    0 normally, 1 for `error: syntax` / `error: unterminated image`,
    3 for `error: image too large`, 2 for any other `error: ...` line.
"""
import json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

TIMEOUT = 10
SAN = re.compile(r"AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer|LeakSanitizer")
CC_BIN = os.path.expanduser("~/envs/cc/bin")


def build(src_dir, official_build_sh, work):
    """Copies src_dir to work/<tree> using the official build.sh; returns binary path or None."""
    tree = os.path.join(work, "tree")
    shutil.copytree(src_dir, tree, symlinks=False)
    b = os.path.join(tree, "tilekit")
    if os.path.lexists(b):
        os.remove(b)
    shutil.copy(official_build_sh, os.path.join(tree, "build.sh"))
    env = dict(os.environ, PATH=CC_BIN + os.pathsep + os.environ.get("PATH", ""))
    try:
        r = subprocess.run(["sh", "build.sh"], cwd=tree, env=env, capture_output=True, timeout=180)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0 or not os.path.isfile(b):
        return None
    return b


def expected_rc(out):
    lines = out.rstrip("\n").split("\n") if out.strip() else []
    last = lines[-1] if lines else ""
    if not last.startswith("error: "):
        return 0
    m = last[7:]
    if m in ("syntax", "unterminated image"):
        return 1
    if m == "image too large":
        return 3
    return 2


def run_test(binary, in_path, out_path):
    with open(in_path, "rb") as f:
        data = f.read()
    with open(out_path, "rb") as f:
        want = f.read().decode("latin-1")
    env = {"PATH": os.environ.get("PATH", ""),
           "ASAN_OPTIONS": "detect_leaks=0:exitcode=99",
           "UBSAN_OPTIONS": "halt_on_error=1:exitcode=99:print_stacktrace=0"}
    with tempfile.TemporaryDirectory() as d:
        try:
            r = subprocess.run([binary], input=data, capture_output=True, timeout=TIMEOUT, cwd=d, env=env)
        except subprocess.TimeoutExpired:
            return False
    if SAN.search(r.stderr.decode("latin-1")):
        return False
    got = r.stdout.decode("latin-1")
    return got == want and r.returncode == expected_rc(want)


def collect(directory):
    if not os.path.isdir(directory):
        return []
    names = sorted(f[:-3] for f in os.listdir(directory) if f.endswith(".in"))
    return [(n, os.path.join(directory, n + ".in"), os.path.join(directory, n + ".out"))
            for n in names if os.path.isfile(os.path.join(directory, n + ".out"))]


def run_set(binary, tests):
    """Returns {name: passed}."""
    if binary is None:
        return {n: False for n, _, _ in tests}
    with ThreadPoolExecutor(max_workers=4) as ex:
        res = list(ex.map(lambda t: run_test(binary, t[1], t[2]), tests))
    return {t[0]: r for t, r in zip(tests, res)}


def main():
    task = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    official = os.path.join(task, "public", "src", "build.sh")
    agent_tests = collect(os.path.join(out, "tests"))
    smoke = collect(os.path.join(task, "public", "smoke"))
    ref_tests = collect(os.path.join(task, "private", "ref_tests"))
    ref_edge = collect(os.path.join(task, "private", "ref_edge"))
    mut_root = os.path.join(task, "private", "mutants")
    mutants = sorted(d for d in os.listdir(mut_root) if os.path.isdir(os.path.join(mut_root, d)))

    details = {"n_agent_tests": len(agent_tests)}
    with tempfile.TemporaryDirectory() as work:
        def mk(sub, src):
            w = os.path.join(work, sub)
            os.makedirs(w)
            return build(src, official, w) if os.path.isdir(src) else None

        orig_bin = mk("orig", os.path.join(task, "public", "src"))
        patch_bin = mk("patch", os.path.join(out, "patch"))
        details["patch_builds"] = patch_bin is not None
        details["original_builds"] = orig_bin is not None

        on_orig = run_set(orig_bin, agent_tests)
        on_patch = run_set(patch_bin, agent_tests) if patch_bin else {n: False for n, _, _ in agent_tests}
        smoke_patch = run_set(patch_bin, smoke)

        ic_tests = 1.0 if (agent_tests and any(not v for v in on_orig.values())
                           and all(on_patch.values()) and patch_bin) else 0.0
        ic_fix = 1.0 if (patch_bin and all(smoke_patch.values()) and all(on_patch.values())) else 0.0
        details["agent_fail_on_original"] = sorted(n for n, v in on_orig.items() if not v)
        details["agent_fail_on_patch"] = sorted(n for n, v in on_patch.items() if not v)
        details["smoke_fail_on_patch"] = sorted(n for n, v in smoke_patch.items() if not v)

        killed = 0
        valid_tests = [t for t in agent_tests if on_patch.get(t[0])]  # only tests the patched build passes
        if valid_tests:
            for m in mutants:
                mb = mk("mut_" + m, os.path.join(mut_root, m))
                res = run_set(mb, valid_tests)
                if mb is not None and any(not v for v in res.values()):
                    killed += 1
                details.setdefault("mutants_killed", {})[m] = bool(mb is not None and any(not v for v in res.values()))
        vc = killed / len(mutants) if (mutants and valid_tests) else 0.0

        rt = run_set(patch_bin, ref_tests)
        re_ = run_set(patch_bin, ref_edge)
        rc_tests = sum(rt.values()) / len(ref_tests) if ref_tests else 0.0
        rc_edge = sum(re_.values()) / len(ref_edge) if ref_edge else 0.0
        details["ref_tests_failed"] = sorted(n for n, v in rt.items() if not v)
        details["ref_edge_failed"] = sorted(n for n, v in re_.items() if not v)

    print(json.dumps({"IC_tests": round(ic_tests, 4), "IC_fix": round(ic_fix, 4), "VC": round(vc, 4),
                      "RC_tests": round(rc_tests, 4), "RC_edge": round(rc_edge, 4), "details": details}))


main()
