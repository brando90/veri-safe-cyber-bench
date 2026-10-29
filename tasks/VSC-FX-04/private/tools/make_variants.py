#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Generate the original (defective) tree, the gold tree and the K=3 mutants
from private/tools/cache.c.tmpl.  Usage: make_variants.py <task_dir>"""
import os
import shutil
import sys

OPEN_FIXED = """\
    unsigned char *payload;

    /* Get the payload first: a failed open must leave the cache untouched. */
    payload = payload_alloc(c, id, size);
    if (!payload) {
        c->st.open_failed++;
        return R_FAILED;
    }
    if (c->count >= CAPACITY) {
        Entry *victim = pick_victim(c);
        if (!victim) {
            payload_free(c, payload, size);
            return R_FULL;
        }
        snprintf(info->evicted, sizeof info->evicted, "%s", victim->id);
        entry_drop(c, victim);
        c->st.evicted++;
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

OPEN_BUGGY = """\
    if (c->count >= CAPACITY) {
        Entry *victim = pick_victim(c);
        if (!victim)
            return R_FULL;
        snprintf(info->evicted, sizeof info->evicted, "%s", victim->id);
        entry_drop(c, victim);
        c->st.evicted++;
    }
    e = calloc(1, sizeof *e);
    if (!e) {
        c->st.open_failed++;
        return R_FAILED;
    }
    snprintf(e->id, sizeof e->id, "%s", id);
    e->size = size;
    e->refs = 1;
    e->last_tick = c->tick;
    hash_insert(c, e);
    lru_push_front(c, e);
    c->count++;
    e->payload = payload_alloc(c, id, size);
    if (!e->payload) {
        /* no payload buffer: give the entry back */
        free(e);
        c->st.open_failed++;
        return R_FAILED;
    }
"""

EVICT_FIXED = "    entry_drop(c, e);\n"
EVICT_BUGGY = """\
    lru_unlink(c, e);
    c->count--;
    entry_destroy(c, e);
"""

SWEEP_FIXED = """\
        if (e->pins > 0) {
            c->st.pinned_skips++;
            (*skipped)++;
            continue;
        }
        report(ctx, e->id);
        entry_drop(c, e);
"""
SWEEP_BUGGY = """\
        report(ctx, e->id);
        hash_remove(c, e);
        lru_unlink(c, e);
        c->count--;
        entry_destroy(c, e);
"""

BLOCKS = {
    "m1_evict_stale_index": ("@@EVICT@@", EVICT_BUGGY),
    "m2_expire_pinned": ("@@SWEEP@@", SWEEP_BUGGY),
    "m3_open_fail_linked": ("@@OPEN_NEW@@", OPEN_BUGGY),
}
FIXED = {"@@EVICT@@": EVICT_FIXED, "@@SWEEP@@": SWEEP_FIXED,
         "@@OPEN_NEW@@": OPEN_FIXED}
FILES = ["sesscache.h", "cmd.c", "main.c", "build.sh", "README.md"]


def render(tmpl, buggy_marks):
    out = tmpl
    for mark, fixed in FIXED.items():
        assert mark in out
        if mark in buggy_marks:
            out = out.replace(mark + "\n", buggy_marks[mark])
        else:
            out = out.replace(mark + "\n", fixed)
    assert "@@" not in out
    return out


def emit(tools, dest, cache_c):
    os.makedirs(dest, exist_ok=True)
    for f in FILES:
        shutil.copy(os.path.join(tools, f), os.path.join(dest, f))
    with open(os.path.join(dest, "cache.c"), "w") as fh:
        fh.write(cache_c)
    os.chmod(os.path.join(dest, "build.sh"), 0o755)


def main():
    task = os.path.abspath(sys.argv[1])
    tools = os.path.join(task, "private", "tools")
    with open(os.path.join(tools, "cache.c.tmpl")) as fh:
        tmpl = fh.read()
    allbug = {m: b for m, b in BLOCKS.values()}
    # original defective tree, shown to the solver (README.md is kept)
    emit(tools, os.path.join(task, "public", "src"), render(tmpl, allbug))
    emit(tools, os.path.join(task, "private", "gold"), render(tmpl, {}))
    for name, (mark, buggy) in BLOCKS.items():
        emit(tools, os.path.join(task, "private", "mutants", name),
             render(tmpl, {mark: buggy}))
    # helper trees used only by the controls
    ctl = os.path.join(task, "private", "controls", "trees")
    emit(tools, os.path.join(ctl, "partial_evict_only"),
         render(tmpl, {m: b for n, (m, b) in BLOCKS.items()
                       if n != "m1_evict_stale_index"}))
    emit(tools, os.path.join(ctl, "partial_evict_expire"),
         render(tmpl, {BLOCKS["m3_open_fail_linked"][0]:
                       BLOCKS["m3_open_fail_linked"][1]}))


if __name__ == "__main__":
    main()
