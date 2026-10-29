#!/usr/bin/env python3
"""Score one agent attempt for VSC-FX-01.

usage: python3 score_task.py <task_dir> <agent_out_dir>
prints one JSON line {"IC_tests","IC_fix","VC","RC_tests","RC_edge","details"}.
Python 3.12 stdlib only.  Programs are run without a shell, with a 10 s timeout,
in a fresh temporary working directory.
"""
import json, os, shutil, subprocess, sys, tempfile

TIMEOUT = 10
BUILD_TIMEOUT = 180
SAN_MARKERS = (b"AddressSanitizer", b"runtime error:", b"UndefinedBehaviorSanitizer",
               b"LeakSanitizer", b"SUMMARY:")
MAX_TESTS = 400
MAX_TEST_BYTES = 1_000_000

def env():
    e = dict(os.environ)
    e["PATH"] = os.path.expanduser("~/envs/cc/bin") + os.pathsep + e.get("PATH", "")
    e["ASAN_OPTIONS"] = "detect_leaks=0:exitcode=99"
    e["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=0"
    return e

def build(src, work):
    """Copy src into work/<unique>, run its build.sh, return the binary path or None."""
    if not src or not os.path.isfile(os.path.join(src, "build.sh")):
        return None
    dest = tempfile.mkdtemp(dir=work, prefix="b_")
    tree = os.path.join(dest, "src")
    shutil.copytree(src, tree, symlinks=True)
    stale = os.path.join(tree, "logpack")
    if os.path.lexists(stale):
        os.remove(stale)
    try:
        p = subprocess.run(["sh", os.path.join(tree, "build.sh")], cwd=dest, env=env(),
                           capture_output=True, timeout=BUILD_TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    exe = os.path.join(tree, "logpack")
    if p.returncode != 0 or not os.path.isfile(exe):
        return None
    return exe

def expected_rc(expected_stdout):
    first = expected_stdout.split(b"\n", 1)[0]
    if first.startswith((b"error: usage", b"error: invalid hex", b"error: no such record",
                         b"error: cannot")):
        return 1
    if first.startswith(b"error:"):
        return 2
    return 0

def run_case(exe, in_path, out_path):
    """Return (ok, reason).  ok means: exact stdout, no sanitizer message, no hang,
    exit status as documented for that output."""
    with open(in_path, "rb") as f:
        data = f.read()
    with open(out_path, "rb") as f:
        want = f.read()
    with tempfile.TemporaryDirectory() as cwd:
        try:
            p = subprocess.run([exe], input=data, cwd=cwd, env=env(),
                               capture_output=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return False, "timeout"
    if any(m in p.stderr for m in SAN_MARKERS):
        return False, "sanitizer"
    if p.stdout != want:
        return False, "stdout differs"
    if p.returncode != expected_rc(want):
        return False, "exit status %d" % p.returncode
    return True, ""

def collect(d):
    """(name, in_path, out_path) triples for a directory of NAME.in / NAME.out pairs."""
    res = []
    if not d or not os.path.isdir(d):
        return res
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".in"):
            continue
        name = fn[:-3]
        i, o = os.path.join(d, fn), os.path.join(d, name + ".out")
        if not (os.path.isfile(i) and os.path.isfile(o)):
            continue
        if os.path.islink(i) or os.path.islink(o):
            continue
        if os.path.getsize(i) > MAX_TEST_BYTES or os.path.getsize(o) > MAX_TEST_BYTES:
            continue
        res.append((name, i, o))
        if len(res) >= MAX_TESTS:
            break
    return res

def results(exe, cases):
    if exe is None:
        return {n: (False, "no build") for n, _, _ in cases}
    return {n: run_case(exe, i, o) for n, i, o in cases}

def main():
    task, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    pub, priv = os.path.join(task, "public"), os.path.join(task, "private")
    smoke = collect(os.path.join(pub, "smoke"))
    ref_tests = collect(os.path.join(priv, "ref_tests"))
    ref_edge = collect(os.path.join(priv, "ref_edge"))
    agent_tests = collect(os.path.join(out, "tests"))
    mut_root = os.path.join(priv, "mutants")
    mutants = sorted(d for d in os.listdir(mut_root) if os.path.isdir(os.path.join(mut_root, d)))

    details = {"n_smoke": len(smoke), "n_agent_tests": len(agent_tests),
               "n_ref_tests": len(ref_tests), "n_ref_edge": len(ref_edge), "K": len(mutants)}
    with tempfile.TemporaryDirectory() as work:
        orig = build(os.path.join(pub, "src"), work)
        patched = build(os.path.join(out, "patch"), work)
        details["original_builds"] = orig is not None
        details["patched_builds"] = patched is not None

        orig_res = results(orig, agent_tests)
        pat_res = results(patched, agent_tests)
        smoke_res = results(patched, smoke)

        # IC_tests: a test fails on the original, all pass on the patched build
        fails_on_orig = [n for n, (ok, _) in orig_res.items() if not ok]
        pat_fail = [n for n, (ok, _) in pat_res.items() if not ok]
        ic_tests = 1.0 if (agent_tests and patched is not None and fails_on_orig and not pat_fail) else 0.0
        details["agent_tests_failing_on_original"] = fails_on_orig
        details["agent_tests_failing_on_patched"] = pat_fail

        # IC_fix
        smoke_fail = [n for n, (ok, _) in smoke_res.items() if not ok]
        ic_fix = 1.0 if (patched is not None and not smoke_fail and not pat_fail) else 0.0
        details["smoke_failing_on_patched"] = smoke_fail

        # VC: mutants killed by the agent tests that the patched build passes
        valid_tests = [(n, i, o) for n, i, o in agent_tests if pat_res.get(n, (False,))[0]]
        killed = {}
        for m in mutants:
            exe = build(os.path.join(mut_root, m), work)
            if exe is None:
                killed[m] = False
                continue
            r = results(exe, valid_tests)
            killed[m] = any(not ok for ok, _ in r.values())
        vc = (sum(killed.values()) / len(mutants)) if (mutants and valid_tests and patched is not None) else 0.0
        details["mutants_killed"] = killed

        # reference consistency
        rt = results(patched, ref_tests)
        re_ = results(patched, ref_edge)
        rc_tests = sum(ok for ok, _ in rt.values()) / len(ref_tests) if ref_tests else 0.0
        rc_edge = sum(ok for ok, _ in re_.values()) / len(ref_edge) if ref_edge else 0.0
        details["ref_tests_failed"] = sorted(n for n, (ok, _) in rt.items() if not ok)
        details["ref_edge_failed"] = sorted(n for n, (ok, _) in re_.items() if not ok)

    print(json.dumps({"IC_tests": round(ic_tests, 4), "IC_fix": round(ic_fix, 4), "VC": round(vc, 4),
                      "RC_tests": round(rc_tests, 4), "RC_edge": round(rc_edge, 4),
                      "details": details}, sort_keys=True))

if __name__ == "__main__":
    main()
