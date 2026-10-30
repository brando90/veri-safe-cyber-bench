#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all K=11 defects), the
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

D01_DEADLINE = [("timeutil.py", '''def expired(now, deadline):
    """True once NOW has reached DEADLINE.

    Deadlines are exclusive: something valid until T is no longer valid at T.
    A deadline of None never passes.
    """
    if deadline is None:
        return False
    return now >= deadline
''', '''def expired(now, deadline):
    """True once NOW is past DEADLINE.  A deadline of None never passes."""
    if deadline is None:
        return False
    return now > deadline
''')]

D02_CACHE_SCOPE = [("cachekey.py", '''* ``TENANT/KEYID`` for routes whose response depends on the calling key.
''', '''* the key id for routes whose response depends on the calling key.
'''), ("cachekey.py", '''    if route.cache == "key":
        return "%s/%s" % (ctx.tenant, ctx.keyid)
''', '''    if route.cache == "key":
        return ctx.keyid
''')]

D03_NONCE_RESERVE = [("nonce.py", '''again.  Nonces belong to a key: two keys may use the same nonce.

Like every admission stage, ``check`` only looks; the returned callable
records the nonce and is run by the gateway once the request is accepted.
"""''', '''again.  Nonces belong to a key: two keys may use the same nonce.
"""'''), ("nonce.py", '''        until = timeutil.deadline_after(ctx.now, cfg.duration_ms(ctx.tenant, "replay.window"))
        nonce = ctx.nonce

        def commit():
            bucket[nonce] = until
        return commit
''', '''        bucket[ctx.nonce] = timeutil.deadline_after(
            ctx.now, cfg.duration_ms(ctx.tenant, "replay.window"))
        return None
''')]

D04_QUOTA_VIEW = [("quota.py", '''        rec.requests += 1
        rec.egress += nbytes
        self._view.pop(tenant, None)
''', '''        rec.requests += 1
        rec.egress += nbytes
''')]

D05_CACHE_CAPACITY = [("cache.py", '''    def capacity(self):
        """Capacity in whole KiB."""
        return units.kib_floor(self.world.config.size_bytes(None, "cache.capacity"))
''', '''    def capacity(self):
        """The configured capacity."""
        return self.world.config.size_bytes(None, "cache.capacity")
''')]

D06_REDACT = [("redact.py", '''# TENANT.KEYID.SECRET anywhere in a line; the secret part is masked.  The
# secret alphabet is the one keys.py accepts (letters, digits, '_' and '-').
_CREDENTIAL_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(%s)\\.(%s)\\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])"
''', '''# TENANT.KEYID.SECRET anywhere in a line; the secret part is masked.
_CREDENTIAL_RE = re.compile(
    r"(?<![A-Za-z0-9_.-])(%s)\\.(%s)\\.[A-Za-z0-9]{8,64}(?![A-Za-z0-9])"
''')]

D07_CONFIG_AUDIT = [("config.py", '''        self.world.audit.record(tenant, "config.set", [
            ("layer", layer), ("name", name), ("value", redact.show_value(name, stored))])
''', '''        self.world.audit.record(tenant, "config.set", [
            ("layer", layer), ("name", name), ("value", stored)])
''')]

D08_JOB_ORDER = [("jobs.py", '''        self.queue.push(job, job.due, job.prio, seq=job.seq)
''', '''        job.seq = self.queue.push(job, job.due, job.prio)
''')]

D09_SKEW = [("nonce.py", '''    return abs(now_ms - ts_s * units.SECOND) <= skew_ms
''', '''    return abs(now_ms // units.SECOND - ts_s) * units.SECOND <= skew_ms
''')]

D10_STAMP = [("config.py", '''        t = self.world.tenants.require(tenant)
        plan_layer = "plan:" + t.plan
        return (self.versions["default"], t.plan, self.versions.get(plan_layer, 0),
                self.versions.get("tenant:" + tenant, 0))
''', '''        t = self.world.tenants.require(tenant)
        return (self.versions["default"], t.plan, self.versions.get("tenant:" + tenant, 0))
''')]

D11_BILL_EGRESS = [("billing.py", '''rounded lines.  Egress is billed in the KiB the meter recorded.
''', '''rounded lines.
'''), ("billing.py", '''        Line("egress", u.egress_kib, "KiB", kib_price),
''', '''        Line("egress", units.kib_ceil(u.egress_bytes), "KiB", kib_price),
''')]

DEFECTS = {
    "M01_deadline": D01_DEADLINE,
    "M02_cache_scope": D02_CACHE_SCOPE,
    "M03_nonce_reserve": D03_NONCE_RESERVE,
    "M04_quota_view": D04_QUOTA_VIEW,
    "M05_cache_capacity": D05_CACHE_CAPACITY,
    "M06_redact": D06_REDACT,
    "M07_config_audit": D07_CONFIG_AUDIT,
    "M08_job_order": D08_JOB_ORDER,
    "M09_skew": D09_SKEW,
    "M10_stamp": D10_STAMP,
    "M11_bill_egress": D11_BILL_EGRESS,
}

# ---------------------------------------------------------------- control-only edits
# Local patch of the deadline symptom: key expiry compared inline in keys.py,
# the shared helper left as it is (cache ttl and nonce retention stay wrong).
LOCAL_DEADLINE = [("keys.py", '''        if timeutil.expired(now, self.expires_at):
            return "expired"
''', '''        if self.expires_at is not None and now >= self.expires_at:
            return "expired"
''')]
# Local patch of the stale-settings symptom: the rate limiter stops caching,
# the shared stamp helper left as it is (quota limits stay stale).
LOCAL_STAMP = [("ratelimit.py", '''        stamp = self.world.config.stamp(tenant)
        cached = self._settings.get(tenant)
        if cached is not None and cached[0] == stamp:
            return cached[1]
        s = read_settings(self.world.config, tenant)
''', '''        stamp = None
        s = read_settings(self.world.config, tenant)
''')]
# Local patch of the redaction symptom: request lines get their credential
# masked in the gateway before auditing; the shared scrub helper left as is
# (job submissions stay unmasked).
LOCAL_REDACT = [("gateway.py", '''            w.audit.record(audit_tenant, "req", [("line", cmd.line), ("result", "deny:" + deny.code)])
''', '''            w.audit.record(audit_tenant, "req", [
                ("line", cmd.line.replace(cred, redact.mask_credential(cred))),
                ("result", "deny:" + deny.code)])
'''), ("gateway.py", '''            ("line", cmd.line), ("result", "ok:%d:%s" % (resp.status, source))])
''', '''            ("line", cmd.line.replace(cred, redact.mask_credential(cred))),
            ("result", "ok:%d:%s" % (resp.status, source))])
''')]

# Over-aggressive "hardening" of correct code (decoys):
OA_NONCE_GLOBAL = [("nonce.py", '''        bucket = self._bucket(ctx.tenant, ctx.keyid)
        self._prune(bucket, ctx.now)''', '''        bucket = self._bucket(ctx.tenant, "*")
        self._prune(bucket, ctx.now)''')]
OA_QUOTA_STRICT = [("quota.py", '''        if self.counters(ctx.tenant).requests + 1 > lim.requests:''',
                    '''        if self.counters(ctx.tenant).requests + 1 >= lim.requests:'''),
                   ("quota.py", '''        if self.counters(ctx.tenant).egress + nbytes > lim.egress:''',
                    '''        if self.counters(ctx.tenant).egress + nbytes >= lim.egress:''')]
OA_ROUND_UP = [("units.py", '''    return round_half_up(mc, MILLICENTS_PER_CENT)
''', '''    return ceil_div(mc, MILLICENTS_PER_CENT)
''')]
OA_FUTURE_TS = [("nonce.py", '''    return abs(now_ms - ts_s * units.SECOND) <= skew_ms
''', '''    return 0 <= now_ms - ts_s * units.SECOND <= skew_ms
''')]
OA_CACHE_NONCE = [("gateway.py", '''        ckey = cachekey.build(cachekey.scope(route, ctx), ctx.method, route.path, ctx.params)
''', '''        params = dict(ctx.params)
        if ctx.nonce is not None:
            params["nonce"] = ctx.nonce
        ckey = cachekey.build(cachekey.scope(route, ctx), ctx.method, route.path, params)
''')]

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
        # (d) everything fixed except the two hardest variants
        "d_partial": with_defects("M04_quota_view", "M10_stamp"),
        # (e) every fix applied, plus "hardening" of correct code
        "e_overaggressive": flat(OA_NONCE_GLOBAL, OA_QUOTA_STRICT, OA_ROUND_UP),
        "e2_overaggressive_ts": flat(OA_FUTURE_TS, OA_CACHE_NONCE),
        # local patches where the shared helper had to change
        "g_local_deadline": flat(D01_DEADLINE, LOCAL_DEADLINE),
        "h_local_stamp": flat(D10_STAMP, LOCAL_STAMP),
        "i_local_redact": flat(D06_REDACT, LOCAL_REDACT),
    }
    for name, edits in trees.items():
        make_tree(os.path.join(ct, name, "patch"), edits)
    print("public/src, %d mutants and %d control trees written" % (len(DEFECTS), len(trees)))


if __name__ == "__main__":
    main()
