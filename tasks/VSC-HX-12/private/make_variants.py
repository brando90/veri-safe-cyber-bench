#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all K=9 defects), the
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

D01_TAG_ACTOR = [("tags.py", '''def _change(w, cmd):
    actor = w.users.actor(cmd.arg(0))
''', '''def _change(w, cmd):
    actor = w.users.get(cmd.arg(0))
''')]

D02_PRUNE_REFUND = [("lifecycle.py", '''        pkg.burned.add(rel.text)
        w.quota.adjust(rel.publisher, -units.kib_ceil(rel.size))
''', '''        pkg.burned.add(rel.text)
        w.quota.adjust(rel.publisher, -(rel.size // units.KIB))
''')]

D03_LATEST_PRE = [("publish.py", '''    if not ver.pre and (cur is None or semver.key(ver) > semver.key(pkg.releases[cur].ver)):
''', '''    if cur is None or semver.key(ver) > semver.key(pkg.releases[cur].ver):
''')]

D04_FETCH_GUARD = [("fetch.py", '''    req = reqs.parse(spec)
    if req is None:
        raise CommandError("bad_req", spec)
    return resolver.best(w, viewer, pkg, [req], req.text)
''', '''    req = reqs.parse(spec)
    return resolver.best(w, viewer, pkg, [req], req.text)
''')]

D05_REMOVE_OWNER = [("accounts.py", '''    target = w.users.get(cmd.arg(1))
    for pkg in w.registry.sorted():
        if pkg.roles.get(target.name) == "owner" and perms.owner_count(pkg) == 1:
            raise CommandError("last_owner", pkg.name)
    dropped = []
''', '''    target = w.users.get(cmd.arg(1))
    dropped = []
''')]

D06_INVITE_DEADLINE = [("owners.py", '''    if timeutil.expired(w.now, inv.expires_at):
        raise CommandError("invite_expired", actor.name, pkg.name)
''', '''    if w.now > inv.expires_at:
        raise CommandError("invite_expired", actor.name, pkg.name)
''')]

D07_TOP_SIZE_ORDER = [("stats.py", '''        rows = rank([(p.name, p.total_kib()) for p in pkgs], n)
''', '''        rows = sorted(((p.name, p.total_kib()) for p in pkgs),
                      key=lambda r: (r[1], r[0]), reverse=True)[:n]
''')]

D08_UNPUBLISH_TAGS = [("lifecycle.py", '''        raise CommandError("grace_over", pkg.name, rel.text, rel.published_at)
    pkg.drop_release(rel.text)
''', '''        raise CommandError("grace_over", pkg.name, rel.text, rel.published_at)
    del pkg.releases[rel.text]
    pkg.recompute_latest()
''')]

D09_DEPENDENTS_VIS = [("info.py", '''        if other is pkg or not other.depends_on(pkg.key):
            continue
        if not perms.can(w, viewer, other, "read"):
            continue
        users.append(other.name)
''', '''        if other is pkg or not other.depends_on(pkg.key):
            continue
        users.append(other.name)
''')]

DEFECTS = {
    "M01_tag_actor": D01_TAG_ACTOR,
    "M02_prune_refund": D02_PRUNE_REFUND,
    "M03_latest_prerelease": D03_LATEST_PRE,
    "M04_fetch_req_guard": D04_FETCH_GUARD,
    "M05_remove_last_owner": D05_REMOVE_OWNER,
    "M06_invite_deadline": D06_INVITE_DEADLINE,
    "M07_top_size_order": D07_TOP_SIZE_ORDER,
    "M08_unpublish_tags": D08_UNPUBLISH_TAGS,
    "M09_dependents_visibility": D09_DEPENDENTS_VIS,
}

# ---------------------------------------------------------------- control-only edits
# Over-aggressive "hardening" of deliberate exceptions listed in policy tables:
OA_PUBLIC_FETCH = [("perms.py", '''PUBLIC_ACTIONS = frozenset({"read", "fetch"})''',
                    '''PUBLIC_ACTIONS = frozenset({"read"})''')]
OA_NO_YANKED_PIN = [("policy.py", '''YANKED_SELECTABLE = frozenset({"exact"})''',
                     '''YANKED_SELECTABLE = frozenset()''')]
OA_PRE_GRACE = [("policy.py", '''    "prerelease": None,''', '''    "prerelease": 72 * HOUR,''')]
OA_NO_EMBARGO_BYPASS = [("policy.py", '''EMBARGO_BYPASS_ROLES = frozenset({"owner", "maintainer"})''',
                         '''EMBARGO_BYPASS_ROLES = frozenset()''')]
OA_ADMIN_NO_OWNER = [("perms.py",
                      '''ADMIN_ACTIONS = frozenset({"yank", "unyank", "unpublish", "owner", "visibility"})''',
                      '''ADMIN_ACTIONS = frozenset({"yank", "unyank", "unpublish"})''')]
OA_UNYANK_MAINTAINER = [("perms.py", '''    "unyank": "owner",''', '''    "unyank": "maintainer",''')]
# Harmonising the invite deadline towards the minority form: the pending
# invite listing changed to the defective accept comparison instead of the
# other way round.
MINORITY_INVITES = [("owners.py", '''               if not timeutil.expired(w.now, pkg.invites[n].expires_at)]''',
                     '''               if not w.now > pkg.invites[n].expires_at]''')]
# Ranking harmonised towards the minority form: every ranking sorts with
# reverse=True on (value, name).
MINORITY_RANK = [("stats.py", '''    return sorted(rows, key=lambda r: (-r[1], r[0]))[:n]''',
                  '''    return sorted(rows, key=lambda r: (r[1], r[0]), reverse=True)[:n]''')]

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
        assert text.count(old) == 1, (dest, fname, old[:70])
        with open(p, "w") as fh:
            fh.write(text.replace(old, new))


def flat(*groups):
    out = []
    for g in groups:
        out.extend(g)
    return out


def with_defects(*names):
    """The edits of the named defects only (a tree where every other one is fixed)."""
    return flat(*(edits for name, edits in DEFECTS.items() if name in names))


def main():
    make_tree(os.path.join(TASK, "public", "src"), flat(*DEFECTS.values()))
    mroot = os.path.join(HERE, "mutants")
    if os.path.exists(mroot):
        shutil.rmtree(mroot)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mroot, name), edits)
    ct = os.path.join(HERE, "controls")
    trees = {
        # (d) everything fixed except the two quietest variants
        "d_partial": with_defects("M01_tag_actor", "M03_latest_prerelease"),
        # (e) every fix applied, plus "hardening" of table-listed exceptions
        "e_overaggressive": flat(OA_PUBLIC_FETCH, OA_NO_YANKED_PIN, OA_PRE_GRACE),
        "e2_overaggressive_roles": flat(OA_NO_EMBARGO_BYPASS, OA_ADMIN_NO_OWNER, OA_UNYANK_MAINTAINER),
        # (g) inconsistencies resolved towards the minority form
        "g_minority_invites": flat(D06_INVITE_DEADLINE, MINORITY_INVITES),
        "h_minority_rank": flat(D07_TOP_SIZE_ORDER, MINORITY_RANK),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
