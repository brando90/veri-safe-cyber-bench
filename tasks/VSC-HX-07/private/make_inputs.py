#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write every .in file (public/smoke, private/ref_tests, private/ref_edge).
Expected .out files are produced from gold by build_private.sh.
Deterministic: the one generated script uses a fixed seed."""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)

# ---------------------------------------------------------------- smoke (valid behaviour only)
SMOKE = {
"s1_keys_and_requests": """# two tenants, their keys and a few requests
tenant add acme
tenant add bolt plan=basic
key issue acme web secret=Wq83kdLm2x label="web shop"
key issue bolt app secret=Zr55plmQ01 ttl=1h
key list acme
req acme.web.Wq83kdLm2x GET /v1/items q.n=4
req acme.web.Wq83kdLm2x GET /v1/items q.n=4
req acme.web.Wq83kdLm2x GET /v1/catalog
req bolt.app.Zr55plmQ01 GET /v1/catalog
req bolt.app.Zr55plmQ01 POST /v1/items
req bolt.app.Zr55plmQ01 GET /v1/nothing
req acme.web.Wrong55secret GET /v1/items
req acme.web.Wq83kdLm2x GET /v1/blob q.size=4KiB
clock advance 2s
usage acme
cache list
""",
"s2_config_layers": """# effective settings come from tenant, plan, default layers
tenant add acme
config get acme rate.limit
config set tenant:acme rate.limit 3
config set default quota.period 1h
config show acme
config explain acme rate.limit
config unset tenant:acme rate.limit
config get acme rate.limit
config set tenant:acme rate.window 0
config set tenant:acme webhook.url https://hooks.example/acme
config layers
""",
"s3_rate_and_quota": """# fixed window rate limit and the request quota
tenant add acme
key issue acme main secret=Kq7m2PzW9a
config set tenant:acme rate.limit 2
config set tenant:acme quota.requests 3
clock set 1000
req acme.main.Kq7m2PzW9a GET /v1/items
req acme.main.Kq7m2PzW9a GET /v1/items q.n=2
req acme.main.Kq7m2PzW9a GET /v1/items q.n=3
clock set 10s
req acme.main.Kq7m2PzW9a GET /v1/items q.n=3
req acme.main.Kq7m2PzW9a GET /v1/items q.n=4
usage acme
""",
"s4_jobs": """# background jobs with a retry
tenant add acme
key issue acme worker secret=Jb44xYq9Rt
job submit acme.worker.Jb44xYq9Rt /v1/report prio=1
job submit acme.worker.Jb44xYq9Rt /v1/report q.fail=2
job submit acme.worker.Jb44xYq9Rt /v1/items delay=5s q.n=2
jobs list
jobs run
clock advance 1s
jobs run
clock advance 2s
jobs run
clock advance 2s
jobs run
jobs list
usage acme
""",
"s5_billing_audit": """# metering, bills and the audit log
tenant add acme plan=basic
key issue acme main secret=Bl88qwErty
req acme.main.Bl88qwErty GET /v1/catalog
req acme.main.Bl88qwErty GET /v1/blob q.size=3KiB
req acme.main.Bl88qwErty GET /v1/blob q.size=3KiB
req acme.main.Bl88qwErty GET /v1/items q.n=7
bill acme
top
audit acme last=3
check
""",
}

# ---------------------------------------------------------------- hidden behaviour tests
A1 = "acme.main.Aa11bb22cc"
REF_TESTS = {
"t01_auth_reasons": """tenant add acme
tenant add bolt
key issue acme main secret=Aa11bb22cc ttl=1m
key issue acme old secret=Dd33ee44ff
key revoke acme old
req acme.main.Aa11bb22cc GET /v1/items
req acme.main.Aa11bb22cX GET /v1/items
req acme.nokey.Aa11bb22cc GET /v1/items
req nobody.main.Aa11bb22cc GET /v1/items
req acme.old.Dd33ee44ff GET /v1/items
req garbage GET /v1/items
req acme..xyz GET /v1/items
tenant suspend acme
req acme.main.Aa11bb22cc GET /v1/items
tenant list
tenant resume acme
req acme.main.Aa11bb22cc GET /v1/items
clock set 2m
req acme.main.Aa11bb22cc GET /v1/items
key list acme
audit acme
report denials
""",
"t02_config_layers_full": """tenant add acme plan=pro
tenant add bolt
config set tenant:acme rate.limit 7
config set tenant:acme rate.window 90000
config set tenant:acme quota.egress 2048
config set tenant:acme cache.capacity 1MiB
config set default cache.capacity 300000
config set plan:nope rate.limit 1
config set tenant:zzz rate.limit 1
config set tenant:acme rate.mode burst
config set tenant:acme jobs.max_attempts 11
config set tenant:acme no.such 1
config load tenant:bolt rate.limit=4 quota.period=1h replay.required=on
config load tenant:bolt rate.limit=9 quota.period=0
config get bolt rate.limit
config get bolt quota.period
config show acme
config explain bolt quota.period
config explain acme cache.capacity
config unset default rate.limit
config unset tenant:acme rate.limit
config unset tenant:acme rate.limit
config explain acme rate.limit
config layers
audit -
audit acme event=config
""",
"t03_rate_fixed_retry": """tenant add acme
key issue acme k1 secret=Rr11ss22tt
key issue acme k2 secret=Uu33vv44ww
config set tenant:acme rate.limit 3
clock set 12300
req acme.k1.Rr11ss22tt GET /v1/items
req acme.k1.Rr11ss22tt GET /v1/items
req acme.k2.Uu33vv44ww GET /v1/items q.n=1
req acme.k1.Rr11ss22tt GET /v1/items
clock set 19001
req acme.k2.Uu33vv44ww GET /v1/items
clock set 20000
req acme.k2.Uu33vv44ww GET /v1/items
rate show acme
usage acme
""",
"t04_rate_sliding_retry": """tenant add acme plan=pro
key issue acme k secret=Ss11ss22ss
config set tenant:acme rate.limit 3
config set tenant:acme rate.window 10s
clock set 1000
req acme.k.Ss11ss22ss GET /v1/items
clock set 2500
req acme.k.Ss11ss22ss GET /v1/items
clock set 4000
req acme.k.Ss11ss22ss GET /v1/items
clock set 5000
req acme.k.Ss11ss22ss GET /v1/items
clock set 10999
req acme.k.Ss11ss22ss GET /v1/items
clock set 11000
req acme.k.Ss11ss22ss GET /v1/items
req acme.k.Ss11ss22ss GET /v1/items
config set tenant:acme rate.limit 4
req acme.k.Ss11ss22ss GET /v1/items
rate show acme
""",
"t05_rate_limit_zero": """tenant add acme
key issue acme k secret=Zz00zz00zz
config set tenant:acme rate.limit 0
req acme.k.Zz00zz00zz GET /v1/items
config set tenant:acme rate.mode sliding
req acme.k.Zz00zz00zz GET /v1/items
config unset tenant:acme rate.limit
req acme.k.Zz00zz00zz GET /v1/items
config unset tenant:acme rate.mode
usage acme
report denials
""",
"t06_quota_exact": """tenant add acme
key issue acme k secret=Qq11qq22qq
config set tenant:acme quota.requests 3
config set tenant:acme quota.egress 3000
config set tenant:acme rate.limit 100
req acme.k.Qq11qq22qq GET /v1/blob q.size=1000
req acme.k.Qq11qq22qq GET /v1/blob q.size=1000
req acme.k.Qq11qq22qq GET /v1/blob q.size=1001
req acme.k.Qq11qq22qq GET /v1/blob q.size=1000
req acme.k.Qq11qq22qq GET /v1/items q.n=1
usage acme
config set tenant:acme quota.period 1h
req acme.k.Qq11qq22qq GET /v1/items q.n=1
usage acme
clock set 1h
usage acme
""",
"t07_nonce_keys": """tenant add acme
tenant add bolt
key issue acme a secret=Na11na22na
key issue acme b secret=Nb11nb22nb
key issue bolt a secret=Nc11nc22nc
clock set 100s
req acme.a.Na11na22na GET /v1/items nonce=n-1 ts=100
req acme.b.Nb11nb22nb GET /v1/items nonce=n-1 ts=100
req bolt.a.Nc11nc22nc GET /v1/items nonce=n-1 ts=100
req acme.a.Na11na22na GET /v1/items nonce=n-1 ts=101
req acme.a.Na11na22na GET /v1/items nonce=n-2 ts=129
req acme.a.Na11na22na GET /v1/items nonce=n-3 ts=69
req acme.a.Na11na22na GET /v1/items nonce=n-3 ts=70
req acme.a.Na11na22na GET /v1/items nonce=n-4
nonce list acme a
nonce list acme b
config set tenant:acme replay.required on
req acme.b.Nb11nb22nb GET /v1/items
req acme.b.Nb11nb22nb GET /v1/items nonce=n-1 ts=100
req acme.b.Nb11nb22nb GET /v1/items nonce=n-9 ts=100
report denials
""",
"t08_cache_identity": """tenant add acme
key issue acme k secret=Ci11ci22ci
config set tenant:acme rate.limit 50
req acme.k.Ci11ci22ci GET /v1/blob q.size=2000 q.tag=x
req acme.k.Ci11ci22ci GET /v1/blob q.tag=x q.size=2000
req acme.k.Ci11ci22ci GET /v1/blob q.size=2000
req acme.k.Ci11ci22ci GET //v1/blob/ q.size=2000
req acme.k.Ci11ci22ci GET /v1/blob q.size=2000 nonce=c1 ts=0
req acme.k.Ci11ci22ci GET /v1/blob q.size=2000 nonce=c2 ts=0
req acme.k.Ci11ci22ci GET /v1/items q.n=abc
req acme.k.Ci11ci22ci GET /v1/items q.n=abc
req acme.k.Ci11ci22ci GET /v1/blob q.size=2MiB
cache list
cache stats
""",
"t09_audit_labels": """tenant add acme
key issue acme front-desk secret=Lb11lb22lb label="Front desk, room 2"
key issue acme ops_1 secret=Lc11lc22lc label=acme.ops.notasecret
key list acme
req acme.front-desk.Lb11lb22lb GET /v1/me
req acme.ops_1.Lc11lc22lc GET /v1/me
req acme.ops_1.Lc11lc22lc GET /v1/me
audit acme
audit export acme format=tsv
audit export acme format=jsonl
""",
"t10_webhook": """tenant add acme
key issue acme w secret=Wh11wh22wh
config set tenant:acme webhook.url https://hooks.example/acme
config set tenant:acme webhook.secret topsecret-1
config set tenant:acme jobs.max_attempts 2
job submit acme.w.Wh11wh22wh /v1/report
job submit acme.w.Wh11wh22wh /v1/report q.fail=9
jobs run
clock advance 1s
jobs run
webhook list acme
config set tenant:acme webhook.secret ""
job submit acme.w.Wh11wh22wh /v1/catalog
jobs run
webhook list acme
webhook clear acme
webhook list acme
config show acme
""",
"t11_bill_rounding": """tenant add acme
tenant add bolt plan=pro
tenant add cobalt plan=basic
key issue acme k secret=Br11br22br
key issue bolt k secret=Bs11bs22bs
config set tenant:acme price.request 1366
config set tenant:acme price.kib 333
config set tenant:bolt price.request 2500
req acme.k.Br11br22br GET /v1/catalog
req acme.k.Br11br22br GET /v1/catalog
req acme.k.Br11br22br GET /v1/catalog
req bolt.k.Bs11bs22bs GET /v1/items q.n=1
bill
bill bolt
top
""",
"t12_jobs_order_prio": """tenant add acme
tenant add bolt
key issue acme k secret=Jo11jo22jo
key issue bolt k secret=Jp11jp22jp
job submit acme.k.Jo11jo22jo /v1/report prio=-1
job submit bolt.k.Jp11jp22jp /v1/report
job submit acme.k.Jo11jo22jo /v1/items prio=5 q.n=1
job submit bolt.k.Jp11jp22jp /v1/catalog delay=1s prio=9
job submit acme.k.Jo11jo22jo /v1/report delay=500
job submit acme.k.Jo11jo22jo /v1/report delay=10s
job cancel j6
job cancel j6
jobs list
jobs run
clock set 1s
jobs list
jobs run
jobs run
job cancel j9
top
""",
"t13_jobs_dead_and_auth": """tenant add acme
key issue acme k secret=Jd11jd22jd ttl=5s
key issue acme r secret=Jr11jr22jr
job submit acme.k.Jd11jd22jd /v1/report q.fail=5
job submit acme.r.Jr11jr22jr /v1/report delay=1s
key revoke acme r
jobs run
clock set 1000
jobs run
clock set 3000
jobs run
job submit acme.k.Jd11jd22jd /v1/report delay=10s
clock set 13000
jobs run
job submit acme.k.Jd11jd22jd /v1/report
key issue acme s secret=Js11js22js
job submit acme.s.Js11js22js /v1/report
tenant suspend acme
jobs run
audit acme event=job
""",
"t14_errors": """bogus
clock set -5
clock set 10s
clock set 5s
clock advance 1x
tenant add 9abc
tenant add acme plan=gold
tenant add acme
tenant add acme
key issue acme k secret=short
key issue acme K secret=Ok11ok22ok
key issue acme k secret=Ok11ok22ok ttl=0
key issue acme k
key issue acme k secret=Ok11ok22ok extra=1
key issue acme k secret=Ok11ok22ok
key issue acme k secret=Ok11ok22ok
req acme.k.Ok11ok22ok PUT /v1/items
req acme.k.Ok11ok22ok GET v1/items
req acme.k.Ok11ok22ok GET /v1/items nonce=x
req acme.k.Ok11ok22ok GET /v1/items ts=1
req acme.k.Ok11ok22ok GET /v1/items nonce=bad! ts=1
req acme.k.Ok11ok22ok GET /v1/items q.n=1 q.n=2
req acme.k.Ok11ok22ok GET /v1/items "unterminated
audit export format=xml
jobs explode
usage nobody
config get acme nothing
job submit acme.k.Ok11ok22ok /v1/report prio=10
job submit acme.k.Ok11ok22ok /v1/report delay=-1
plan list
plan show
""",
"t16_post_purges_cache": """tenant add acme
tenant add bolt
key issue acme k secret=Pp11pp22pp
key issue bolt k secret=Pq11pq22pq
req acme.k.Pp11pp22pp GET /v1/items
req acme.k.Pp11pp22pp GET /v1/items
req bolt.k.Pq11pq22pq GET /v1/items
req acme.k.Pp11pp22pp POST /v1/items
req acme.k.Pp11pp22pp GET /v1/items
req bolt.k.Pq11pq22pq GET /v1/items
cache purge bolt
req bolt.k.Pq11pq22pq GET /v1/items
cache list
audit bolt event=cache
""",
"t17_plan_switch": """tenant add acme
key issue acme k secret=Ps11ps22ps
config set tenant:acme rate.window 1m
req acme.k.Ps11ps22ps GET /v1/items q.n=1
req acme.k.Ps11ps22ps GET /v1/items q.n=2
req acme.k.Ps11ps22ps GET /v1/items q.n=3
req acme.k.Ps11ps22ps GET /v1/items q.n=4
req acme.k.Ps11ps22ps GET /v1/items q.n=5
req acme.k.Ps11ps22ps GET /v1/items q.n=6
tenant plan acme basic
req acme.k.Ps11ps22ps GET /v1/items q.n=6
usage acme
tenant plan acme pro
rate show acme
bill acme
plan list
""",
"t18_default_layer_change": """tenant add acme plan=basic
key issue acme k secret=Dl11dl22dl
config set default rate.window 1m
req acme.k.Dl11dl22dl GET /v1/items q.n=1
req acme.k.Dl11dl22dl GET /v1/items q.n=2
req acme.k.Dl11dl22dl GET /v1/items q.n=3
config set default quota.requests 2
config set tenant:acme quota.requests 4
req acme.k.Dl11dl22dl GET /v1/items q.n=4
req acme.k.Dl11dl22dl GET /v1/items q.n=5
config set default rate.limit 1
config set tenant:acme quota.requests 10
req acme.k.Dl11dl22dl GET /v1/items q.n=5
config set default rate.limit 4
req acme.k.Dl11dl22dl GET /v1/items q.n=5
config set default cache.ttl 0
req acme.k.Dl11dl22dl GET /v1/catalog
usage acme
""",
"t19_key_rotate": """tenant add acme
key issue acme k secret=Ro11ro22ro ttl=1h
req acme.k.Ro11ro22ro GET /v1/me
key rotate acme k secret=Ro33ro44ro
req acme.k.Ro11ro22ro GET /v1/me
req acme.k.Ro33ro44ro GET /v1/me
key revoke acme k
key rotate acme k secret=Ro55ro66ro
key show acme k
key show acme zz
audit acme event=key
""",
"t20_reports": """tenant add acme
tenant add bolt plan=pro
key issue acme k secret=Rp11rp22rp ttl=90s
key issue acme j secret=Rq11rq22rq ttl=1h
key issue bolt k secret=Rs11rs22rs
config set tenant:acme rate.limit 2
req acme.k.Rp11rp22rp GET /v1/items
req acme.k.Rp11rp22rp GET /v1/items
req acme.k.Rp11rp22rp GET /v1/items
req acme.k.Rp11rp22rp GET /v1/items nonce=z ts=500
req bolt.k.Rs11rs22rs GET /v1/catalog
req bolt.k.Rs11rs22rs GET /v1/catalog
req bolt.k.WrongWrong1 GET /v1/catalog
job submit bolt.k.Rs11rs22rs /v1/report delay=1h
report denials
report tenant acme
report tenant bolt
stats
top
check
""",
"t21_units_display": """clock set 1500ms
clock advance 1m
clock advance 2h
clock
tenant add acme
config set tenant:acme rate.window 3600000
config set tenant:acme rate.window 61s
config set tenant:acme rate.window 2h
config set tenant:acme quota.egress 1048576
config set tenant:acme quota.egress 1025
config set tenant:acme cache.ttl 0
config set tenant:acme quota.period 2d
config set tenant:acme quota.period 31d
config set tenant:acme replay.skew 1500
config set tenant:acme replay.required yes
config show acme
""",
"t22_capacity_oversize": """config set default cache.capacity 4KiB
tenant add acme
key issue acme k secret=Co11co22co
req acme.k.Co11co22co GET /v1/blob q.size=5000
req acme.k.Co11co22co GET /v1/blob q.size=5000
req acme.k.Co11co22co GET /v1/blob q.size=4096
req acme.k.Co11co22co GET /v1/blob q.size=4096
cache stats
cache list
""",
"t23_shared_ttl": """tenant add acme plan=pro
tenant add bolt
key issue acme k secret=Sh11sh22sh
key issue bolt k secret=Si11si22si
req acme.k.Sh11sh22sh GET /v1/catalog
clock set 20s
req bolt.k.Si11si22si GET /v1/catalog
clock set 40s
req acme.k.Sh11sh22sh GET /v1/catalog
req acme.k.Sh11sh22sh GET /v1/items
clock set 100s
req acme.k.Sh11sh22sh GET /v1/items
cache list
""",
"t24_meter_hits": """tenant add acme
key issue acme k secret=Mh11mh22mh
req acme.k.Mh11mh22mh GET /v1/blob q.size=1500
req acme.k.Mh11mh22mh GET /v1/blob q.size=1500
usage acme
bill acme
""",
"t25_export_escaping": """tenant add acme
key issue acme k secret=Ex11ex22ex label="tab\there \\back"
key list acme
req acme.k.Ex11ex22ex GET /v1/me
audit export acme format=tsv
audit export acme format=jsonl
audit export format=tsv
""",
"t26_help": """help
help key
help setting quota.egress
help setting backend.token
help setting replay.required
help setting jobs.backoff
help setting nope
help zzz
""",
}

# ---------------------------------------------------------------- hidden edge tests
REF_EDGE = {
"e01_key_expiry_boundary": """tenant add acme
key issue acme k secret=Ke11ke22ke ttl=10s
clock set 9999
req acme.k.Ke11ke22ke GET /v1/items
clock set 10000
req acme.k.Ke11ke22ke GET /v1/items
key list acme
""",
"e02_cache_ttl_boundary": """tenant add acme
key issue acme k secret=Ca11ca22ca
config set tenant:acme rate.limit 50
req acme.k.Ca11ca22ca GET /v1/items
clock set 29999
req acme.k.Ca11ca22ca GET /v1/items
clock set 30000
req acme.k.Ca11ca22ca GET /v1/items
cache list
""",
"e03_nonce_window_boundary": """tenant add acme
key issue acme k secret=No11no22no
config set tenant:acme replay.window 1m
req acme.k.No11no22no GET /v1/items nonce=r1 ts=0
clock set 59999
req acme.k.No11no22no GET /v1/items nonce=r1 ts=59
clock set 60000
req acme.k.No11no22no GET /v1/items nonce=r1 ts=60
nonce list acme k
""",
"e04_me_same_keyid_two_tenants": """tenant add acme
tenant add bolt
key issue acme main secret=Me11me22me label=acme-desk
key issue bolt main secret=Mf11mf22mf label=bolt-desk
req acme.main.Me11me22me GET /v1/me
req bolt.main.Mf11mf22mf GET /v1/me
req bolt.main.Mf11mf22mf GET /v1/me
""",
"e05_me_cache_scopes": """tenant add acme
tenant add bolt plan=basic
tenant add cobalt plan=pro
key issue acme ops secret=Sc11sc22sc
key issue acme dev secret=Sd11sd22sd
key issue bolt ops secret=Se11se22se
key issue cobalt ops secret=Sf11sf22sf
req acme.ops.Sc11sc22sc GET /v1/me
req acme.dev.Sd11sd22sd GET /v1/me
req cobalt.ops.Sf11sf22sf GET /v1/me
req bolt.ops.Se11se22se GET /v1/me
req acme.ops.Sc11sc22sc GET /v1/me
""",
"e06_nonce_kept_after_rate_deny": """tenant add acme
key issue acme k secret=Nr11nr22nr
config set tenant:acme rate.limit 1
req acme.k.Nr11nr22nr GET /v1/items nonce=a1 ts=0
req acme.k.Nr11nr22nr GET /v1/items nonce=a2 ts=0
clock set 10s
req acme.k.Nr11nr22nr GET /v1/items nonce=a2 ts=10
nonce list acme k
""",
"e07_nonce_kept_after_egress_deny": """tenant add acme
key issue acme k secret=Ne11ne22ne
config set tenant:acme quota.egress 2KiB
req acme.k.Ne11ne22ne GET /v1/blob q.size=3KiB nonce=b1 ts=0
req acme.k.Ne11ne22ne GET /v1/blob q.size=1KiB nonce=b1 ts=0
nonce list acme k
usage acme
""",
"e08_jobs_batch_request_quota": """tenant add acme
key issue acme w secret=Qb11qb22qb
config set tenant:acme quota.requests 3
req acme.w.Qb11qb22qb GET /v1/items
job submit acme.w.Qb11qb22qb /v1/report
job submit acme.w.Qb11qb22qb /v1/report
job submit acme.w.Qb11qb22qb /v1/report
jobs run
usage acme
""",
"e09_jobs_batch_egress_quota": """tenant add acme
tenant add bolt
key issue acme w secret=Qe11qe22qe
key issue bolt w secret=Qf11qf22qf
config set tenant:acme quota.egress 4000
job submit acme.w.Qe11qe22qe /v1/report
job submit bolt.w.Qf11qf22qf /v1/report
job submit acme.w.Qe11qe22qe /v1/report
job submit acme.w.Qe11qe22qe /v1/report
jobs run
usage acme
usage bolt
""",
"e10_cache_capacity_eviction": """config set default cache.capacity 4KiB
tenant add acme
key issue acme k secret=Ce11ce22ce
config set tenant:acme rate.limit 50
req acme.k.Ce11ce22ce GET /v1/blob q.size=2000
req acme.k.Ce11ce22ce GET /v1/blob q.size=2001
req acme.k.Ce11ce22ce GET /v1/blob q.size=2002
req acme.k.Ce11ce22ce GET /v1/blob q.size=2000
cache stats
cache list
""",
"e11_cache_capacity_not_multiple": """config set default cache.capacity 5000
tenant add acme
key issue acme k secret=Cf11cf22cf
req acme.k.Cf11cf22cf GET /v1/blob q.size=1500
req acme.k.Cf11cf22cf GET /v1/blob q.size=1501
req acme.k.Cf11cf22cf GET /v1/blob q.size=1502
req acme.k.Cf11cf22cf GET /v1/blob q.size=1500
cache stats
""",
"e12_audit_secret_dash": """tenant add acme
key issue acme k secret=Kx-4471-qq
req acme.k.Kx-4471-qq GET /v1/items
req acme.k.Kx-4471-qX GET /v1/items
audit acme
""",
"e13_job_submit_secret_underscore": """tenant add acme
key issue acme batch secret=job_runner_77
job submit acme.batch.job_runner_77 /v1/report
jobs run
audit export acme format=tsv
""",
"e14_config_sensitive_audit": """tenant add acme
config set tenant:acme backend.token tk-998877
config set default webhook.secret base-secret
config get acme backend.token
audit acme
audit -
""",
"e15_config_load_sensitive_audit": """tenant add acme
config load tenant:acme webhook.url=https://hooks.example/a webhook.secret=wh-5521
audit acme event=config
audit export acme format=jsonl
""",
"e16_retry_keeps_submission_order": """tenant add acme
key issue acme w secret=Or11or22or
job submit acme.w.Or11or22or /v1/report q.fail=1
job submit acme.w.Or11or22or /v1/report delay=1000
jobs run
clock set 1000
jobs list
jobs run
""",
"e17_retry_order_three_jobs": """tenant add acme
key issue acme w secret=Os11os22os
job submit acme.w.Os11os22os /v1/report q.fail=1
job submit acme.w.Os11os22os /v1/report q.fail=1
job submit acme.w.Os11os22os /v1/report delay=1s
job submit acme.w.Os11os22os /v1/catalog delay=1s prio=1
jobs run
clock set 1s
jobs run
""",
"e18_skew_past_boundary": """tenant add acme
key issue acme k secret=Sk11sk22sk
config set tenant:acme replay.skew 5s
clock set 15999
req acme.k.Sk11sk22sk GET /v1/items nonce=s1 ts=10
req acme.k.Sk11sk22sk GET /v1/items nonce=s2 ts=11
clock set 16000
req acme.k.Sk11sk22sk GET /v1/items nonce=s3 ts=11
""",
"e19_skew_future_subsecond": """tenant add acme
key issue acme k secret=Sl11sl22sl
config set tenant:acme replay.skew 5500ms
clock set 4400
req acme.k.Sl11sl22sl GET /v1/items nonce=f0 ts=10
clock set 4600
req acme.k.Sl11sl22sl GET /v1/items nonce=f1 ts=10
""",
"e20_plan_layer_rate_limit": """tenant add acme
key issue acme k secret=Pl11pl22pl
req acme.k.Pl11pl22pl GET /v1/items q.n=1
req acme.k.Pl11pl22pl GET /v1/items q.n=2
config set plan:free rate.limit 2
req acme.k.Pl11pl22pl GET /v1/items q.n=3
usage acme
""",
"e21_plan_layer_quota": """tenant add acme plan=basic
key issue acme k secret=Pm11pm22pm
req acme.k.Pm11pm22pm GET /v1/items q.n=1
req acme.k.Pm11pm22pm GET /v1/items q.n=2
req acme.k.Pm11pm22pm GET /v1/items q.n=3
config set plan:basic quota.requests 3
req acme.k.Pm11pm22pm GET /v1/items q.n=4
usage acme
""",
"e22_bill_egress_per_response": """tenant add acme
key issue acme k secret=Be11be22be
config set tenant:acme cache.ttl 0
req acme.k.Be11be22be GET /v1/blob q.size=1100
req acme.k.Be11be22be GET /v1/blob q.size=1100
req acme.k.Be11be22be GET /v1/blob q.size=1100
bill acme
""",
"e23_bill_hits_and_jobs": """tenant add acme plan=pro
key issue acme k secret=Bh11bh22bh
req acme.k.Bh11bh22bh GET /v1/items q.n=3
req acme.k.Bh11bh22bh GET /v1/items q.n=3
job submit acme.k.Bh11bh22bh /v1/report
jobs run
req acme.k.Bh11bh22bh GET /v1/blob q.size=0
bill acme
usage acme
""",
}


def big_script():
    """t15: a few thousand ordinary commands (performance and ordering)."""
    rng = random.Random(7)
    out = ["tenant add acme plan=pro", "tenant add bolt plan=basic", "tenant add cobalt",
           "key issue acme a secret=Bg11bg22bg", "key issue acme b secret=Bg33bg44bg",
           "key issue bolt a secret=Bh33bh44bh", "key issue cobalt a secret=Bi55bi66bi",
           "config set tenant:cobalt quota.requests 400",
           "config set default cache.capacity 64KiB"]
    creds = ["acme.a.Bg11bg22bg", "acme.b.Bg33bg44bg", "bolt.a.Bh33bh44bh", "cobalt.a.Bi55bi66bi"]
    paths = ["/v1/items q.n=%d", "/v1/blob q.size=%d", "/v1/catalog", "/v1/me", "/v1/report"]
    t = 0
    for i in range(3200):
        t += rng.choice((0, 0, 100, 500, 1000, 2500))
        if i % 40 == 0:
            out.append("clock set %d" % t)
        cred = rng.choice(creds)
        p = rng.choice(paths)
        if "%d" in p:
            p = p % (rng.randint(1, 20) if "items" in p else rng.randint(1, 30) * 300)
        if i % 97 == 5:
            out.append("job submit %s %s" % (cred, p.split(" ")[0]))
        elif i % 113 == 7:
            out.append("jobs run")
        else:
            out.append("req %s GET %s" % (cred, p))
    out += ["usage acme", "usage bolt", "usage cobalt", "bill", "top", "cache stats",
            "report denials", "stats", "audit acme last=5", "jobs list", "check"]
    return "\n".join(out) + "\n"


REF_TESTS["t15_big_script"] = big_script()


def write(directory, cases):
    os.makedirs(directory, exist_ok=True)
    for f in os.listdir(directory):
        if f.endswith(".in") or f.endswith(".out"):
            os.remove(os.path.join(directory, f))
    for name, text in cases.items():
        with open(os.path.join(directory, name + ".in"), "w") as fh:
            fh.write(text)


def main():
    write(os.path.join(TASK, "public", "smoke"), SMOKE)
    write(os.path.join(HERE, "ref_tests"), REF_TESTS)
    write(os.path.join(HERE, "ref_edge"), REF_EDGE)
    print("inputs: smoke=%d ref_tests=%d ref_edge=%d" % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    main()
