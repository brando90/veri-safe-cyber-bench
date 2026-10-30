# VSC-HX-07 author notes (private)

quotagate: toy multi-tenant API-gateway simulator. 33 Python modules (about
3,000 lines) plus a 290-line README that is the specification. One `World`
wires the components; every command runs at one logical instant; admission
stages (auth -> nonce -> rate -> request quota -> cache/upstream -> egress
quota) only look and hand back commit callables that the gateway runs once
the request is accepted; quotas are read through a per-command view
(`Quota.begin_command`) that `commit` must invalidate; components that cache
derived settings (rate limiter, quota limits, cache ttl) compare
`Config.stamp(tenant)`; the consistency check (invariant.py, exit 86)
re-reads configuration freshly and checks quota/rate counters, cache
accounting, queue and meter sanity. `legacy.py` is dead v1 code.

## The defects (K = 11, one mutant each in private/mutants)

| Mutant | Where | Defect | README rule it breaks | Kind |
|---|---|---|---|---|
| M01_deadline | timeutil.expired (shared by keys, cache, nonce) | `now > deadline` instead of `now >= deadline`; keys, cache entries and remembered nonces stay valid at their deadline | Time: "Deadlines are exclusive" (+ key, cache and nonce sections) | time boundary; shared helper (a local fix in keys.py leaves cache and nonce wrong) |
| M02_cache_scope | cachekey.scope | per-key routes scoped by key id only; key ids are unique only within a tenant, so `/v1/me` of tenant B's `main` is served tenant A's cached response | Cache isolation; "key id unique within that tenant" | tenant isolation via shared cache key |
| M03_nonce_reserve | nonce.NonceStore.check | records the nonce during the look phase instead of returning a commit; a request refused later (rate, quota-requests, quota-egress) has used up its nonce | "A refused request changes nothing ... does not use up its nonce" | check-then-commit gap across gateway/nonce/quota; state carried between calls |
| M04_quota_view | quota.Quota.commit | does not drop the per-command view after counting; inside one `jobs run` batch later jobs see the counters as they were at the start of the command, so the batch overruns quota.requests / quota.egress (invariant fires) | "quota rules apply to every job of a batch exactly as ... one command at a time" | state carried between calls; jobs -> gateway -> quota -> invariant |
| M05_cache_capacity | cache.Cache.capacity | returns bytes while `used` is in KiB; eviction never happens below 1024x capacity (invariant on accounting) or capacity not a KiB multiple mishandled | Cache capacity: entries in whole KiB rounded up, capacity rounded down | unit mismatch bytes vs KiB (config -> cache -> units -> invariant) |
| M06_redact | redact._CREDENTIAL_RE | secret class `[A-Za-z0-9]{8,64}` while keys accept `_` and `-`; such credentials reach audit lines and exports unmasked | Secrets: any text of credential shape has its third part masked; secret alphabet in Keys | secrets echoed; shared helper (masking in the gateway only leaves job submissions) |
| M07_config_audit | config.Config.set | audit record of `config.set` stores the raw value instead of `redact.show_value`; `backend.token` / `webhook.secret` appear in `audit` and exports | Secrets: sensitive setting values shown as `***` wherever they appear | secrets echoed (config -> audit; scrub only knows credential shapes) |
| M08_job_order | jobs.JobRunner._retry | a retried job is pushed with a fresh sequence number, so it runs after jobs submitted later with the same due time and prio | Jobs: "A job put back for a retry keeps its submission order" | ordering stability (pqueue tie-break) |
| M09_skew | nonce.is_fresh | compares whole seconds (`now_ms // 1000 - ts`) * 1000 with the skew; accepts up to 999 ms too much in one direction, refuses valid ts in the other | Replay: distance measured in milliseconds; ts=12 means 12000 ms | unit conversion / truncation (s vs ms) |
| M10_stamp | config.Config.stamp | stamp omits the plan layer's version; a `config set plan:P ...` is ignored by the cached rate settings and quota limits until something else changes (invariant fires) | "Changes take effect immediately ... any layer" | state; shared helper (dropping the rate limiter's cache leaves quota limits stale) |
| M11_bill_egress | billing.lines | egress line uses KiB of the summed bytes instead of the meter's per-response KiB | Metering: egress per response, each rounded up | rounding convention differs between meter and billing |

Coverage of the v3 rules:
* Findable by reading one function (with the README): M01, M02, M09 (3).
* Need data/state across 3+ modules: M03, M04, M05, M06, M10, M11 (also M07: config -> audit -> redact).
* Time / ordering / state / number convention: M01, M04, M05, M08, M09, M10, M11.
* Shared helper must change (local patch wrong): M01 (control g), M10 (control h), M06 (control i).

## Intended fix (= private/gold)

* `timeutil.expired`: `now >= deadline`.
* `cachekey.scope`: `TENANT/KEYID` for per-key routes.
* `nonce.check`: only looks; returns a commit that records the nonce.
* `quota.commit`: `self._view.pop(tenant, None)` after counting.
* `cache.capacity`: `units.kib_floor(config.size_bytes(None, "cache.capacity"))`.
* `redact._CREDENTIAL_RE`: secret class `[A-Za-z0-9_-]+` with matching lookahead.
* `config.set` audit: `redact.show_value(name, stored)`.
* `jobs._retry`: `queue.push(job, due, prio, seq=job.seq)`.
* `nonce.is_fresh`: `abs(now_ms - ts_s * 1000) <= skew_ms`.
* `config.stamp`: include `versions["plan:" + plan]`.
* `billing.lines`: egress quantity = `usage.egress_kib` (per-response KiB from the meter).

## Traps (each caught by a hidden case; see private/CONTROLS.md)

1. Local deadline fix in keys.py only: e02 (cache ttl boundary), e03 (nonce window boundary) fail: control g.
2. Dropping the rate limiter's settings cache instead of fixing the stamp: e21 (plan-layer quota change) fails: control h.
3. Masking the credential in the gateway's audit call instead of fixing the scrub pattern: e13 (job submission audit) fails: control i.
4. Making nonces global per tenant ("hardening"): t07 fails (two keys may use the same nonce).
5. Refusing a quota at the limit (`>=`): t06 (reaching a limit exactly is allowed), smoke s3 and more.
6. Rounding money up instead of half up: t11 and smoke s5.
7. Refusing future `ts` ("only past timestamps"): t07 (ts within skew in the future) fails: control e2.
8. Putting nonce into the cache key: t08 (requests differing only in nonce are the same request): control e2.
9. Fixing M08 by making retried jobs run first (e.g. prio bump): e17 has a prio=1 job that must still run first and a later submission that must run after.
10. Fixing M05 by converting capacity to KiB with ceil: e11 (capacity 5000 bytes holds 4 KiB, not 5).
11. Fixing M09 by rounding instead of exact ms: e18/e19 hit both sides of the boundary.
12. Fixing M03 only for the rate stage: e07 (egress refusal is decided after the upstream call).
13. Fixing M04 by re-checking only quota.requests: e09 (egress across a batch, with another tenant's job in between).

## Decoys (correct code that looks suspicious)

* `quota.check`: `requests + 1 > limit` / `egress + n > limit` (reaching the limit exactly is allowed; t06).
* `ratelimit`: `len(inside) >= s.limit` with `rate.limit` 0 refusing everything (documented; t05).
* Nonces stored per key, not per tenant (documented; t07).
* `nonce.is_fresh` symmetric `abs(...) <= skew` accepting future ts (documented; t07, e19).
* Cache key sorts `q.` params and leaves out nonce/ts (documented; t08).
* Audit shows key ids and labels in clear; scrub masks label text of credential shape (`acme.ops.***`, documented "any text of that shape"; t09).
* Webhook signatures printed (`sig=`): derived, not the secret (module docstring; t10).
* `units.kib_floor` for capacity vs `kib_ceil` for entries (documented asymmetry; t22, e10/e11).
* `units.round_half_up` per bill line (documented; t11).
* `legacy.kb_decimal` dividing by 1000: dead v1 code, never called.
* `backend.bad_request` echoes the parameter value in the 400 body (parameters are not secrets).
* `admin.quota_reset` pokes `quota._current` / `_view` directly (and clears the view correctly).

## Notes

* Original passes every smoke case and fails all 23 ref_edge cases; it also fails 5 ref_tests (t13, t15, t17, t22, t24) whose ordinary scenarios touch a defect. Each mutant fails only its own ref_edge cases plus at most three ref_tests, and no smoke case (check_variants.py).
* Inputs come from private/make_inputs.py; outputs from private/build_private.sh (gold run in a fresh dir); public/src, mutants and control patch trees from private/make_variants.py (exact-text edits of gold). t15 is a 3,200-command generated script (fixed seed), about 1 s on gold.
* `help` (helptext.py) is documentation only; t26 pins its output.
* Smoke cases avoid every trigger: no boundary instants, no key id shared between tenants on `/v1/me`, secrets without `_`/`-`, no sensitive config followed by audit, no retry ties, no plan-layer changes, no capacity pressure, no batch quota exhaustion, at most one non-KiB-multiple response before a bill.
