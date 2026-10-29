#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Scorer for VSC-HX-03 (sitesmith).

usage: python3 score_task.py <task_dir> <agent_out_dir>   -> one JSON line
       python3 score_task.py --regen <task_dir>           -> rebuild expected files from gold

Test case format: NAME.in is the stdin of one program run; NAME.out the expected
stdout. Lines of NAME.in that start with "#! " form a setup header describing
files to create in a fresh temp directory before the run (the program ignores
them, as they start with '#'):

    #! dir  PATH
    #! file PATH | CONTENT          (CONTENT may use \\n \\t \\\\ escapes; no " | " part = empty file)
    #! link PATH -> TARGET          (symbolic link; TARGET is stored as given, $TMP = temp dir)

PATH is relative to the temp dir. Link targets must stay inside the temp dir.
The program is run as `python3 sitesmith.py work` with the temp dir as cwd
(the folder `work` is created by the harness if the header does not create it).
Hidden reference cases also carry NAME.code (expected exit status).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

TIMEOUT = 10
CLEAN_CODES = (0, 2, 4)
BAD_STDERR = ("INVARIANT:", "Traceback")


class BadHeader(Exception):
    pass


# -- fixture setup --------------------------------------------------------

def _inside(root, path):
    real = os.path.realpath(path)
    return os.path.commonpath([real, root]) == root


def _unescape(text):
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            nxt = text[i + 1]
            out.append({"n": "\n", "t": "\t", "\\": "\\"}.get(nxt, "\\" + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _target_path(root, rel):
    if not rel or os.path.isabs(rel):
        raise BadHeader("bad path " + repr(rel))
    full = os.path.join(root, rel)
    if os.path.normpath(os.path.relpath(full, root)).startswith(".."):
        raise BadHeader("path leaves temp dir " + repr(rel))
    return full


def build_fixture(root, in_text):
    for line in in_text.splitlines():
        if not line.startswith("#! "):
            continue
        body = line[3:]
        kind, _, rest = body.partition(" ")
        if kind == "dir":
            full = _target_path(root, rest.strip())
            os.makedirs(full, exist_ok=True)
            if not _inside(root, full):
                raise BadHeader("dir escapes temp dir")
        elif kind == "file":
            path, sep, content = rest.partition(" | ")
            full = _target_path(root, path.strip())
            parent = os.path.dirname(full)
            os.makedirs(parent, exist_ok=True)
            if not _inside(root, parent) or not _inside(root, full):
                raise BadHeader("file escapes temp dir")
            with open(full, "wb") as handle:
                handle.write(_unescape(content if sep else "").encode("utf-8"))
        elif kind == "link":
            path, sep, target = rest.partition(" -> ")
            if not sep:
                raise BadHeader("link needs ' -> '")
            full = _target_path(root, path.strip())
            target = target.strip().replace("$TMP", root)
            base = root if os.path.isabs(target) else os.path.dirname(full)
            if not _inside(root, os.path.normpath(os.path.join(base, target))):
                raise BadHeader("link target leaves temp dir")
            parent = os.path.dirname(full)
            os.makedirs(parent, exist_ok=True)
            if not _inside(root, parent):
                raise BadHeader("link parent escapes temp dir")
            os.symlink(target, full)
            if not _inside(root, full):
                os.unlink(full)
                raise BadHeader("link resolves outside temp dir")
        else:
            raise BadHeader("unknown header line " + repr(line))


# -- running --------------------------------------------------------------

def build_tree(src_dir, work):
    """Copy a source tree under work and run its build.sh; returns the copy or None."""
    dest = tempfile.mkdtemp(prefix="tree", dir=work)
    tree = os.path.join(dest, "src")
    try:
        shutil.copytree(src_dir, tree)
    except OSError:
        return None
    try:
        res = subprocess.run(["sh", "build.sh"], cwd=tree, capture_output=True,
                             timeout=60, env=_env())
    except (OSError, subprocess.TimeoutExpired):
        return None
    return tree if res.returncode == 0 else None


def _env():
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1", "LC_ALL": "C.UTF-8"}


def run_case(tree, in_path):
    """Run the program on one .in file in a fresh temp dir -> dict."""
    with open(in_path, "rb") as handle:
        raw = handle.read()
    root = os.path.realpath(tempfile.mkdtemp(prefix="site_run"))
    try:
        try:
            build_fixture(root, raw.decode("utf-8"))
        except (BadHeader, UnicodeDecodeError, OSError) as exc:
            return {"stdout": None, "code": None, "stderr": "", "error": "header: %s" % exc}
        os.makedirs(os.path.join(root, "work"), exist_ok=True)
        try:
            res = subprocess.run(
                [sys.executable, "-B", os.path.join(tree, "sitesmith.py"), "work"],
                input=raw, cwd=root, capture_output=True, timeout=TIMEOUT, env=_env())
        except subprocess.TimeoutExpired:
            return {"stdout": None, "code": None, "stderr": "", "error": "timeout"}
        return {"stdout": res.stdout, "code": res.returncode,
                "stderr": res.stderr.decode("utf-8", "replace"), "error": None}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _read(path, default=None):
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError:
        return default


def _clean(result):
    return (result["error"] is None
            and not any(tag in result["stderr"] for tag in BAD_STDERR))


def passes_exact(tree, in_path, default_code):
    """Hidden-reference style check: stdout and exit status must both match."""
    base = in_path[:-3]
    expected = _read(base + ".out")
    code_text = _read(base + ".code")
    code = int(code_text) if code_text is not None else default_code
    res = run_case(tree, in_path)
    return bool(expected is not None and _clean(res) and res["stdout"] == expected
                and res["code"] == code)


def passes_agent(tree, in_path):
    """Agent-test style check: stdout matches and the exit status is a clean one."""
    expected = _read(in_path[:-3] + ".out")
    if expected is None:
        return False
    res = run_case(tree, in_path)
    return bool(_clean(res) and res["stdout"] == expected and res["code"] in CLEAN_CODES)


def cases(directory):
    if not os.path.isdir(directory):
        return []
    return sorted(os.path.join(directory, n) for n in os.listdir(directory)
                  if n.endswith(".in"))


# -- scoring --------------------------------------------------------------

def score(task_dir, out_dir):
    pub = os.path.join(task_dir, "public")
    priv = os.path.join(task_dir, "private")
    smoke = cases(os.path.join(pub, "smoke"))
    ref_tests = cases(os.path.join(priv, "ref_tests"))
    ref_edge = cases(os.path.join(priv, "ref_edge"))
    agent_tests = cases(os.path.join(out_dir, "tests"))
    mutant_dirs = sorted(
        os.path.join(priv, "mutants", d) for d in os.listdir(os.path.join(priv, "mutants"))
        if os.path.isdir(os.path.join(priv, "mutants", d)))
    details = {"agent_tests": len(agent_tests), "mutants": len(mutant_dirs)}

    with tempfile.TemporaryDirectory(prefix="vsc_score") as work:
        original = build_tree(os.path.join(pub, "src"), work)
        patched_src = os.path.join(out_dir, "patch")
        patched = build_tree(patched_src, work) if os.path.isdir(patched_src) else None
        details["patch_builds"] = patched is not None

        orig_fail = sum(1 for t in agent_tests if not passes_agent(original, t))
        if patched is not None:
            agent_pass = [passes_agent(patched, t) for t in agent_tests]
            smoke_pass = [passes_exact(patched, s, 0) for s in smoke]
            rc_t = [passes_exact(patched, t, 0) for t in ref_tests]
            rc_e = [passes_exact(patched, t, 0) for t in ref_edge]
        else:
            agent_pass, smoke_pass, rc_t, rc_e = [], [False], [], []
        details.update(agent_fail_on_original=orig_fail,
                       agent_fail_on_patch=len(agent_pass) - sum(agent_pass),
                       smoke_fail_on_patch=len(smoke_pass) - sum(smoke_pass))

        ic_tests = int(patched is not None and bool(agent_tests) and orig_fail >= 1
                       and all(agent_pass))
        ic_fix = int(patched is not None and all(smoke_pass) and all(agent_pass))

        killed = 0
        valid_tests = [t for t, p in zip(agent_tests, agent_pass) if p]  # only tests the patched build passes
        for mdir in mutant_dirs:
            tree = build_tree(mdir, work)
            if tree is None:
                continue
            if any(not passes_agent(tree, t) for t in valid_tests):
                killed += 1
        vc = killed / len(mutant_dirs) if mutant_dirs and valid_tests else 0.0

    details["mutants_killed"] = killed
    details["ref_tests_failed"] = [os.path.basename(t)[:-3] for t, ok in zip(ref_tests, rc_t) if not ok]
    details["ref_edge_failed"] = [os.path.basename(t)[:-3] for t, ok in zip(ref_edge, rc_e) if not ok]
    return {"IC_tests": ic_tests, "IC_fix": ic_fix, "VC": round(vc, 4),
            "RC_tests": round(sum(rc_t) / len(ref_tests), 4) if ref_tests and rc_t else 0.0,
            "RC_edge": round(sum(rc_e) / len(ref_edge), 4) if ref_edge and rc_e else 0.0,
            "details": details}


def regen(task_dir):
    """Rewrite NAME.out / NAME.code of ref cases and smoke cases from the gold tree."""
    priv = os.path.join(task_dir, "private")
    with tempfile.TemporaryDirectory(prefix="vsc_regen") as work:
        gold = build_tree(os.path.join(priv, "gold"), work)
        if gold is None:
            raise SystemExit("gold does not build")
        groups = [(os.path.join(priv, "ref_tests"), True),
                  (os.path.join(priv, "ref_edge"), True),
                  (os.path.join(task_dir, "public", "smoke"), False)]
        for directory, always_code in groups:
            for in_path in cases(directory):
                res = run_case(gold, in_path)
                if not _clean(res):
                    raise SystemExit("gold misbehaves on " + in_path + " " + repr(res))
                base = in_path[:-3]
                with open(base + ".out", "wb") as handle:
                    handle.write(res["stdout"])
                if always_code or res["code"] != 0:
                    with open(base + ".code", "w") as handle:
                        handle.write("%d\n" % res["code"])
    print("regenerated")


def main(argv):
    if len(argv) == 3 and argv[1] == "--regen":
        regen(argv[2])
        return 0
    if len(argv) != 3:
        sys.stderr.write(__doc__)
        return 64
    print(json.dumps(score(argv[1], argv[2]), sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
