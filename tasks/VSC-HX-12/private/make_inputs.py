#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write every .in file (public/smoke, private/ref_tests, private/ref_edge).
Expected .out files are produced from gold by build_private.sh.
Deterministic: the one generated script uses a fixed seed."""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

# ---------------------------------------------------------------- smoke (ordinary behaviour only)
SMOKE = {
"s1_publish_resolve": """# publishing, resolving and fetching
user add alice
user add bob
publish alice left-pad 1.0.0 size=2KiB
publish alice left-pad 1.2.0 size=2500
publish alice left-pad 1.10.1 size=3KiB
publish bob tiny-json 0.4.2 size=900
resolve - left-pad ^1.0
resolve - left-pad ~1.2.0
resolve bob tiny-json ^0.4
fetch bob left-pad
fetch - left-pad >=1.2.0,<1.10.0
fetch - Left_Pad 1.0
info - left-pad
tags - left-pad
quota alice
""",
"s2_roles_invites": """# roles and invites
user add alice
user add bob
user add carol
publish alice api-kit 2.0.0 size=10KiB
owner invite alice api-kit bob
owner invite alice api-kit carol role=reader ttl=2d
invites alice api-kit
clock advance 1h
owner accept bob api-kit
roles - api-kit
publish bob api-kit 2.1.0 size=10KiB
owner remove alice api-kit bob
publish bob api-kit 2.2.0
roles carol api-kit
invites alice api-kit
owner accept carol api-kit
roles - api-kit
user show carol
quota bob
""",
"s3_yank_unpublish": """# yank, deprecate, unpublish
user add alice
user add bob
publish alice csv-tool 1.0.0 size=4KiB
publish alice csv-tool 1.1.0 size=5000
publish alice csv-tool 1.2.0 size=8KiB
owner invite alice csv-tool bob
owner accept bob csv-tool
yank bob csv-tool 1.2.0 reason="wrong output"
tags - csv-tool
resolve - csv-tool ^1.0
deprecate alice csv-tool 1.0.0 message="use 1.1"
fetch - csv-tool =1.0.0
unyank alice csv-tool 1.2.0
unpublish alice csv-tool 1.1.0
publish alice csv-tool 1.1.0
quota alice
clock advance 3d
unpublish alice csv-tool 1.0.0
info - csv-tool
""",
"s4_lock_and_reports": """# dependencies, a lock and the reports
user add alice
user add bob
user add carol
publish alice base 1.0.0 size=1KiB
publish alice base 1.4.0 size=2KiB
publish bob http 2.0.0 size=6KiB deps=base@^1.2
publish carol cli 0.9.0 size=3KiB deps=http@^2;base@>=1.0
fetch - base
fetch - base
fetch - http
lock carol app cli@*
dependents - base
top - downloads
top - releases
top - dependents
search - ba
publish alice base 1.5.0 size=2KiB
outdated carol app
""",
"s5_audit_errors": """# refused commands, the audit log and the export
user add root admin
user add alice
publish alice Fast_Hash 1.0.0 size=1500
publish alice fast-hash 1.0.0
publish alice core 1.0.0
publish alice fast.hash 1.0.x
resolve - nothing ^1
frobnicate now
publish alice fast-hash 1.1.0 colour=red
yank alice fast-hash 1.0.0 reason="bad, very bad"
audit n=3
export audit tsv
check
""",
}

# ---------------------------------------------------------------- hidden behaviour tests
REF_TESTS = {
"t01_requirement_forms": """user add alice
publish alice num 0.0.3
publish alice num 0.0.4
publish alice num 0.2.1
publish alice num 0.2.9
publish alice num 0.3.0
publish alice num 1.0.0
publish alice num 1.2.0
publish alice num 1.2.7
publish alice num 1.3.0
publish alice num 2.0.0
resolve - num ^1.2
resolve - num ~1.2.0
resolve - num ~1
resolve - num >=1.0,<1.3
resolve - num *
resolve - num =1.2.0
resolve - num ^0.2.1
resolve - num ^0.0.3
resolve - num 1
resolve - num >1.2.7,<=2.0.0
resolve - num <0.1
resolve - num ^3
""",
"t02_semver_order": """user add alice
publish alice ver 1.9.0
publish alice ver 1.10.0
publish alice ver 1.10.0-rc.1
publish alice ver 1.10.0-rc.10
publish alice ver 1.10.0-rc.2
publish alice ver 1.10.0-alpha
publish alice ver 1.2.0
info - ver
tags - ver
resolve - ver ^1
resolve - ver >=1.10.0-rc.1
resolve - ver >=1.10.0-rc.1,<1.10.0
resolve - ver =1.10.0-alpha
""",
"t03_public_fetch_anonymous": """user add alice
user add bob
publish alice pub-lib 1.0.0 size=1KiB
publish alice priv-lib 1.0.0 size=1KiB visibility=private
fetch - pub-lib
fetch bob pub-lib ^1
fetch - priv-lib
fetch bob priv-lib
resolve - priv-lib *
info bob priv-lib
info - pub-lib
tags bob priv-lib
roles bob priv-lib
""",
"t04_private_visibility": """user add alice
user add bob
user add carol
publish alice hidden-x 1.0.0 size=1KiB visibility=private
publish alice shown-x 1.0.0 size=1KiB
owner invite alice hidden-x bob role=reader
owner accept bob hidden-x
search carol x
search bob x
top carol releases
top bob releases
info bob hidden-x
yank bob hidden-x 1.0.0
yank carol hidden-x 1.0.0
publish carol hidden-x 1.1.0
publish carol shown-x 1.1.0
visibility alice hidden-x public
search carol x
""",
"t05_admin_actions": """user add root admin
user add alice
publish alice owned 1.0.0 size=1KiB
publish alice owned 1.1.0 size=1KiB
yank root owned 1.1.0 reason=policy
unyank root owned 1.1.0
unpublish root owned 1.1.0
tag add root owned stable 1.0.0
publish root owned 1.2.0
owner invite root owned root role=owner
owner accept root owned
tag add root owned stable 1.0.0
visibility root owned private
roles alice owned
quota alice
""",
"t06_prerelease_unpublish_late": """user add alice
publish alice tool 1.0.0 size=1KiB
publish alice tool 1.1.0-rc.1 size=1KiB
clock advance 100h
unpublish alice tool 1.1.0-rc.1
unpublish alice tool 1.0.0
publish alice tool 1.1.0-rc.1
publish alice tool 1.1.0-rc.2
info - tool
""",
"t07_yanked_exact_pin": """user add alice
publish alice pin 1.0.0
publish alice pin 1.1.0
yank alice pin 1.1.0 reason="data loss"
resolve - pin ^1.0
resolve - pin =1.1.0
resolve - pin >=1.1.0
fetch - pin =1.1.0
lock - l pin@=1.1.0
lock - l2 pin@^1
tags - pin
""",
"t08_embargo_roles": """user add alice
user add bob
user add carol
user add dave
publish alice sec 1.0.0
owner invite alice sec bob
owner accept bob sec
owner invite alice sec dave role=reader
owner accept dave sec
clock set 1000
publish alice sec 1.1.0 embargo=2h
resolve carol sec ^1
resolve bob sec ^1
resolve dave sec ^1
resolve carol sec =1.1.0
fetch carol sec
info alice sec
clock set 8199
resolve carol sec ^1
clock set 8200
resolve carol sec ^1
fetch carol sec
""",
"t09_invite_ttl_limits": """user add alice
user add bob
user add carol
publish alice inv 1.0.0
owner invite alice inv bob role=owner ttl=3d
owner invite alice inv bob role=owner ttl=2d
owner invite alice inv carol role=reader ttl=20d
owner invite alice inv carol role=admin
owner invite alice inv alice role=owner
invites alice inv
clock advance 1d
owner accept carol inv
owner accept bob inv
roles - inv
invites alice inv
""",
"t10_unyank_owner_only": """user add alice
user add bob
publish alice yk 1.0.0
publish alice yk 1.1.0
owner invite alice yk bob
owner accept bob yk
yank bob yk 1.1.0
yank bob yk 1.1.0
unyank bob yk 1.1.0
unpublish bob yk 1.0.0
unyank alice yk 1.1.0
unyank alice yk 1.1.0
tags - yk
""",
"t11_managed_latest_tag": """user add alice
publish alice tg 1.0.0
publish alice tg 1.1.0
tag add alice tg latest 1.0.0
tag rm alice tg latest
tag add alice tg Bad_Tag 1.0.0
tag add alice tg old 1.0.0
tag add alice tg old 1.1.0
tag rm alice tg nope
tags - tg
audit n=2
""",
"t12_quota_limits": """user add root admin
user add alice
quota set root alice 10
publish alice big 1.0.0 size=4KiB
publish alice big 1.1.0 size=5000
publish alice big 1.2.0 size=1
publish alice big 1.3.0 size=1
quota alice
unpublish alice big 1.1.0
quota alice
publish alice big 1.3.0 size=5KiB
quota set alice alice 99
package delete root big
quota alice
publish alice big 2.0.0 size=10KiB
quota alice
""",
"t13_last_owner_rules": """user add alice
user add bob
publish alice lo 1.0.0
owner remove alice lo alice
owner invite alice lo bob role=owner
owner accept bob lo
owner remove bob lo alice
owner remove bob lo bob
owner invite bob lo bob role=reader
owner accept bob lo
roles - lo
owner remove bob lo carol
owner remove bob lo alice
""",
"t14_lock_conflict": """user add alice
publish alice a 1.0.0
publish alice a 1.5.0
publish alice a 2.0.0
publish alice b 1.0.0 deps=a@^1.2
publish alice c 1.0.0 deps=a@^2
publish alice d 1.0.0 deps=b@^1;a@>=1.0
lock alice good d@^1
lock alice bad b@* c@*
lock alice pinned a@=1.0.0
lock alice mixed d@* a@<1.6
lock alice broken d@^1 b
""",
"t15_big_script": None,
"t16_error_table": """user add alice
user add Alice
user add alice
user add bob admin extra
publish alice x-1 1.0.0 size=12q
publish alice x-1 1.0.0 embargo=soon
publish alice x-1 1.0.0 visibility=secret
publish alice -bad 1.0.0
publish alice registry 1.0.0
publish alice x-1 01.0.0
publish alice x-1 1.0.0 deps=nothing@^1
publish alice x-1 1.0.0 deps=x-1@^1
publish alice x-1 1.0.0 deps=junk
publish alice x-1 1.0.0
publish alice x-1 1.0.0
unpublish alice x-1 1.0.0
publish alice x-1 1.0.0
publish alice x-2 1.0.0 deps=x-1@^1;X_1@^1
yank alice x-1 9.9.9
publish nobody x-1 2.0.0
clock set 50
clock set 10
clock advance 1w
publish alice x-1 2.0.0 size=1 size=2
publish alice "x-1 2.0.0
tag add alice x-1
top - weird
export audit xml
quota set alice alice 5
help nothing
""",
"t17_audit_export": """user add alice
publish alice esc 1.0.0
yank alice esc 1.0.0 reason="a\\b, c\td"
deprecate alice esc 1.0.0 message=" padded "
audit
export audit tsv
export audit csv
""",
"t18_disable_enable": """user add root admin
user add alice
user add bob
publish alice dz 1.0.0
user disable root alice
publish alice dz 1.1.0
yank alice dz 1.0.0
fetch alice dz
info alice dz
owner invite alice dz bob
user disable root alice
user disable alice root
user show alice
user enable root alice
user enable root alice
publish alice dz 1.1.0
user disable bob alice
fetch - dz
""",
"t19_outdated": """user add alice
publish alice o1 1.0.0
publish alice o2 1.0.0
publish alice o3 1.0.0
lock - set o1@^1 o2@^1 o3@^1
publish alice o1 1.1.0
yank alice o2 1.0.0
unpublish alice o3 1.0.0
outdated - set
outdated - nothing
""",
"t20_top_ties": """user add alice
user add bob
publish alice kb 1.0.0
publish bob ka 1.0.0
publish alice kc 1.0.0 deps=ka@^1;kb@^1
publish bob kd 1.0.0 deps=kb@^1
publish bob ka 1.1.0
publish alice kb 1.1.0
fetch - kc
fetch - ka
fetch - kd
top - downloads
top - releases
top - dependents
top - downloads n=2
top - releases n=0
""",
"t21_canonical_names": """user add alice
user add bob
publish alice My_Lib 1.0.0
publish bob my-lib 1.1.0
publish alice my.lib 1.1.0
fetch - MY-LIB
info - my__lib
search - My.L
roles - mY-lIb
lock - n my_lib@^1
""",
"t22_help": """help
help publish
help owner invite
""",
"t23_deprecate_notes": """user add alice
publish alice dep 1.0.0
publish alice dep 1.1.0
deprecate alice dep 1.1.0 message="moved to dep2"
fetch - dep
resolve - dep ^1
info - dep
deprecate alice dep 1.1.0
fetch - dep
""",
"t24_prune_whole_kib": """user add root admin
user add alice
publish alice pr 1.0.0 size=2KiB
publish alice pr 1.1.0 size=3KiB
publish alice pr 1.2.0 size=1KiB
tag add alice pr old 1.0.0
yank alice pr 1.0.0
yank alice pr 1.1.0
prune alice pr
prune root pr
tags - pr
quota alice
publish alice pr 1.1.0
prune root pr
""",
"t25_dependency_visibility": """user add alice
user add bob
publish alice inner 1.0.0 visibility=private
publish bob outer 1.0.0 deps=inner@^1
owner invite alice inner bob role=reader
owner accept bob inner
publish bob outer 1.0.0 deps=inner@^1
lock bob l outer@*
lock - l outer@*
fetch - outer
""",
}

# ---------------------------------------------------------------- hidden edge tests (fail on the original)
REF_EDGE = {
"e01_disabled_user_tag_add": """user add root admin
user add alice
user add bob
publish alice left-pad 1.0.0 size=1KiB
publish alice left-pad 1.1.0 size=1KiB
owner invite alice left-pad bob
owner accept bob left-pad
tag add bob left-pad stable 1.0.0
user disable root bob
tag add bob left-pad next 1.1.0
publish bob left-pad 1.2.0
tags - left-pad
user enable root bob
tag add bob left-pad next 1.1.0
tags - left-pad
""",
"e02_disabled_user_tag_rm": """user add root admin
user add alice
publish alice web-kit 3.0.0
tag add alice web-kit lts 3.0.0
user disable root alice
tag rm alice web-kit lts
tags - web-kit
audit n=2
""",
"e03_prune_refund_partial_kib": """user add root admin
user add alice
publish alice blob 1.0.0 size=1500
publish alice blob 1.1.0 size=2KiB
yank alice blob 1.0.0
prune root blob
quota alice
check
""",
"e04_prune_refund_small": """user add root admin
user add bob
quota set root bob 3
publish bob tiny 0.1.0 size=1
publish bob tiny 0.2.0 size=1
publish bob tiny 0.3.0 size=1
yank bob tiny 0.1.0
yank bob tiny 0.2.0
prune root tiny
publish bob tiny 0.4.0 size=1
publish bob tiny 0.5.0 size=1
quota bob
""",
"e05_prerelease_not_latest": """user add alice
user add bob
publish alice orm 1.4.0 size=1KiB
publish alice orm 2.0.0-beta.1 size=1KiB
tags - orm
fetch bob orm
search - orm
publish alice orm 1.5.0 size=1KiB
tags - orm
info bob orm
""",
"e06_first_release_prerelease": """user add alice
publish alice newlib 0.1.0-alpha.1
tags - newlib
fetch - newlib
fetch - newlib >=0.1.0-alpha.0
info - newlib
yank alice newlib 0.1.0-alpha.1
unyank alice newlib 0.1.0-alpha.1
tags - newlib
""",
"e07_fetch_bad_requirement": """user add alice
publish alice parser 1.0.0
fetch - parser ^1.x
fetch - parser 1.0.0
""",
"e08_fetch_bad_requirement_forms": """user add alice
user add bob
publish alice parser 1.0.0
publish alice parser 1.2.0
resolve bob parser >=1.0,<
fetch bob parser >=1.0,<
fetch bob parser =1.2
fetch bob parser 1.2.0.0
lock bob l1 parser@=1.2
fetch bob parser =1.2.0
info - parser
""",
"e09_remove_sole_owner": """user add root admin
user add alice
user add bob
publish alice solo 1.0.0
owner invite alice solo bob
owner accept bob solo
user remove root alice
user show alice
roles - solo
check
""",
"e10_remove_user_mixed": """user add root admin
user add alice
user add bob
publish alice shared 1.0.0
publish alice mine 1.0.0
owner invite alice shared bob role=owner
owner accept bob shared
user remove root alice
roles - shared
roles - mine
owner invite alice mine bob role=owner
owner accept bob mine
user remove root alice
roles - shared
roles - mine
user show alice
""",
"e11_invite_accept_at_deadline": """user add alice
user add bob
publish alice cfg 1.0.0
owner invite alice cfg bob
clock set 86399
invites alice cfg
clock set 86400
invites alice cfg
owner accept bob cfg
roles - cfg
""",
"e12_invite_custom_ttl_boundary": """user add alice
user add bob
user add carol
publish alice cfg 1.0.0
clock set 100
owner invite alice cfg bob role=reader ttl=10m
owner invite alice cfg carol role=owner ttl=2d
clock advance 10m
owner accept bob cfg
clock set 172900
owner accept carol cfg
roles - cfg
""",
"e13_top_size_ties": """user add alice
user add bob
publish alice zeta 1.0.0 size=2KiB
publish bob alpha 1.0.0 size=2KiB
publish alice mid 1.0.0 size=5KiB
publish bob beta 1.0.0 size=1500
top - size
top - releases
""",
"e14_top_size_cutoff": """user add alice
publish alice c-lib 1.0.0 size=3KiB
publish alice a-lib 1.0.0 size=1KiB
publish alice a-lib 1.1.0 size=2KiB
publish alice b-lib 1.0.0 size=3KiB
top - size n=1
top - size n=2
""",
"e15_unpublish_tagged_release": """user add alice
publish alice sdk 1.0.0 size=1KiB
publish alice sdk 1.1.0 size=1KiB
publish alice sdk 2.0.0 size=1KiB
tag add alice sdk next 1.1.0
unpublish alice sdk 1.1.0
tags - sdk
check
""",
"e16_unpublish_prerelease_tag": """user add alice
user add bob
publish alice sdk 1.0.0 size=1KiB
publish alice sdk 2.0.0-rc.1 size=1KiB
tag add alice sdk rc 2.0.0-rc.1
tag add alice sdk stable 1.0.0
clock advance 5d
unpublish alice sdk 2.0.0-rc.1
fetch bob sdk @rc
fetch bob sdk @stable
tags - sdk
""",
"e17_dependents_private_hidden": """user add alice
user add bob
user add carol
publish alice log-core 1.0.0
publish bob secret-app 0.1.0 deps=log-core@^1 visibility=private
publish carol open-app 0.2.0 deps=log-core@^1
dependents carol log-core
dependents bob log-core
top carol dependents
""",
"e18_dependents_anonymous": """user add alice
user add bob
publish alice json 2.0.0
publish alice json-schema 1.0.0 deps=json@^2 visibility=private
owner invite alice json-schema bob role=reader
owner accept bob json-schema
dependents - json
dependents bob json
visibility alice json-schema public
dependents - json
""",
}


def big_script(seed=1207, n=1600):
    """A long ordinary session: publishing, fetching, tags, roles, locks."""
    rng = random.Random(seed)
    users = ["u%d" % i for i in range(1, 9)]
    lines = ["# generated session (seed %d)" % seed]
    lines += ["user add %s" % u for u in users]
    pkgs = {}
    order = []
    while len(lines) < n:
        roll = rng.random()
        if roll < 0.08 or len(order) < 4:
            name = "pk%02d" % len(order)
            if name in pkgs or len(order) >= 24:
                continue
            owner = rng.choice(users)
            deps = ""
            if order and rng.random() < 0.6:
                picks = rng.sample(order, min(len(order), rng.randint(1, 2)))
                deps = " deps=" + ";".join("%s@^%d" % (p, pkgs[p]["vers"][0][0]) for p in picks)
            pkgs[name] = {"owner": owner, "members": [owner], "vers": [(1, 0, 0)], "yanked": set()}
            order.append(name)
            lines.append("publish %s %s 1.0.0 size=%d%s" % (owner, name, rng.randint(0, 9000), deps))
        elif roll < 0.30:
            name = rng.choice(order)
            p = pkgs[name]
            ma, mi, pa = p["vers"][-1]
            step = rng.random()
            nv = (ma + 1, 0, 0) if step < 0.1 else (ma, mi + 1, 0) if step < 0.5 else (ma, mi, pa + 1)
            p["vers"].append(nv)
            who = rng.choice(p["members"])
            lines.append("publish %s %s %d.%d.%d size=%d" % ((who, name) + nv + (rng.randint(0, 12000),)))
        elif roll < 0.55:
            name = rng.choice(order)
            ma = rng.choice(pkgs[name]["vers"])[0]
            viewer = rng.choice(users + ["-"])
            lines.append("fetch %s %s ^%d" % (viewer, name, ma))
        elif roll < 0.62:
            name = rng.choice(order)
            lines.append("fetch - %s" % name)
        elif roll < 0.68:
            name = rng.choice(order)
            p = pkgs[name]
            v = rng.choice(p["vers"])
            text = "%d.%d.%d" % v
            if text in p["yanked"]:
                lines.append("unyank %s %s %s" % (p["owner"], name, text))
                p["yanked"].discard(text)
            else:
                lines.append("yank %s %s %s reason=r%d" % (rng.choice(p["members"]), name, text, rng.randint(1, 99)))
                p["yanked"].add(text)
        elif roll < 0.73:
            name = rng.choice(order)
            p = pkgs[name]
            lines.append("tag add %s %s next %d.%d.%d" % ((p["owner"], name) + rng.choice(p["vers"])))
        elif roll < 0.77:
            name = rng.choice(order)
            p = pkgs[name]
            other = rng.choice(users)
            if other in p["members"]:
                continue
            lines.append("owner invite %s %s %s" % (p["owner"], name, other))
            lines.append("owner accept %s %s" % (other, name))
            p["members"].append(other)
        elif roll < 0.82:
            lines.append("clock advance %dm" % rng.randint(1, 600))
        elif roll < 0.86:
            roots = rng.sample(order, min(3, len(order)))
            lines.append("lock %s set%d %s" % (rng.choice(users), len(lines),
                                               " ".join("%s@*" % r for r in roots)))
        elif roll < 0.90:
            lines.append("top - %s n=%d" % (rng.choice(["downloads", "releases", "dependents"]),
                                            rng.randint(3, 8)))
        elif roll < 0.94:
            name = rng.choice(order)
            lines.append("resolve - %s ~%d.%d" % ((name,) + rng.choice(pkgs[name]["vers"])[:2]))
        elif roll < 0.97:
            lines.append("info - %s" % rng.choice(order))
        else:
            lines.append("quota %s" % rng.choice(users))
    lines.append("check")
    lines.append("audit n=15")
    return "\n".join(lines) + "\n"


def write(directory, cases):
    os.makedirs(directory, exist_ok=True)
    for name in list(os.listdir(directory)):
        if name.endswith(".in") and name[:-3] not in cases:
            os.remove(os.path.join(directory, name))
            out = os.path.join(directory, name[:-3] + ".out")
            if os.path.exists(out):
                os.remove(out)
    for name, text in cases.items():
        with open(os.path.join(directory, name + ".in"), "w") as f:
            f.write(text)


def main():
    REF_TESTS["t15_big_script"] = big_script()
    write(os.path.join(TASK, "public", "smoke"), SMOKE)
    write(os.path.join(HERE, "ref_tests"), REF_TESTS)
    write(os.path.join(HERE, "ref_edge"), REF_EDGE)
    print("inputs written: %d smoke, %d ref_tests, %d ref_edge" % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    main()
