#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive public/src (the original program with all defects), the K=12
mutants (gold plus exactly one defect each) and the patch trees of the
scorer controls from private/gold.  Deterministic, stdlib only.  Every edit
is an exact, unique text replacement, so a drift in gold makes this script
fail loudly."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")

# ---------------------------------------------------------------- defects
# Each defect: list of (file, gold text, defective text).

D01_RETRY_PLACE = [("dispatch.py", '''                else:
                    frag.not_before = decision.at
                    svc.stats.bump("retries")
''', '''                else:
                    frag.not_before = decision.at
                    svc.queue.take(entry)
                    svc.queue.add(msg, frag)
                    svc.stats.bump("retries")
''')]

D02_TURN_STAMP = [("queueing.py", '''        self._services += 1
        self._turn[sender] = self._services
''', '''        self._services += 1
        self._turn[sender] = now
''')]

D03_WINDOW_EDGE = [("timewin.py", '''    return now - earlier < width_ms
''', '''    return now - earlier <= width_ms
''')]

D04_TTL_RETRY_EDGE = [("retry.py", '''    if at >= msg.deadline:
        return Decision(EXPIRE)
''', '''    if at > msg.deadline:
        return Decision(EXPIRE)
''')]

D05_BUSY_UNITS = [("dispatch.py", '''                hint = units.s_to_ms(outcome.after_s)
''', '''                hint = outcome.after_s
''')]

D06_KIB_SCALE = [("units.py", '''SIZE_SCALE = {"bytes": 1, "kib": BYTES_PER_KIB}
''', '''SIZE_SCALE = {"bytes": 1, "kib": BYTES_PER_KB}
''')]

D07_BATCH_CAPACITY = [("commands.py", '''    svc.sender(toks[1])
    svc.recipient(toks[2])
    for n, item in enumerate(block, 1):
''', '''    svc.sender(toks[1])
    svc.recipient(toks[2])
    if not intake.has_room(svc, toks[2]):
        raise CommandError("recipient %s has no room" % toks[2])
    for n, item in enumerate(block, 1):
'''), ("commands.py", '''            intake.submit(svc, req)
        except CommandError as exc:
''', '''            intake.submit(svc, req, room_checked=True)
        except CommandError as exc:
'''), ("intake.py", '''def submit(svc, req):
    """Run REQ through the acceptance checks.  Returns the Message or None."""
''', '''def submit(svc, req, room_checked=False):
    """Run REQ through the acceptance checks.  Returns the Message or None.
    ROOM_CHECKED: the caller has already checked the recipient's capacity."""
'''), ("intake.py", '''    if not has_room(svc, req.recipient):
        svc.stats.bump("rejected")
''', '''    if not room_checked and not has_room(svc, req.recipient):
        svc.stats.bump("rejected")
''')]

D08_DIRECT_RESET = [("dispatch.py", '''        outcome = self.begin(entry, t)
        self.settle(entry, t, outcome, direct=False)
''', '''        outcome = self.begin(entry, t)
        if outcome.acked:
            self.svc.breaker.on_success(r)
        self.settle(entry, t, outcome, direct=False)
'''), ("dispatch.py", '''            svc.queue.take(entry)
            svc.breaker.on_success(r)
        else:
''', '''            svc.queue.take(entry)
        else:
''')]

D09_REASSEMBLY_DUP = [("reassembly.py", '''        if index in self.parts:
            return False
        self.parts[index] = data
''', '''        self.parts[index] = data
''')]

D10_DEDUP_REJECTED = [("intake.py", '''    earlier = svc.dedup.find(key, now, cfg.ms("dedup.window_s", req.recipient))
''', '''    earlier = svc.dedup.check(key, now, cfg.ms("dedup.window_s", req.recipient), req.id)
'''), ("intake.py", '''    svc.dedup.remember(key, now, msg.id)
''', '''''')]

D11_MONEY_TOTAL = [("money.py", '''    return sum(cents(a) for a in amounts)
''', '''    return cents(sum(amounts, Fraction(0)))
''')]

D12_DIRECT_LIMITS = [("intake.py", '''    if svc.pending_for(r) != 1 or svc.breaker.paused(r):
        return False
    if svc.limits.block_reason(svc.cfg, r, svc.offset_of(r), svc.now, msg.size) is not None:
        return False
''', '''    if svc.pending_for(r) != 1 or svc.breaker.paused(r):
        return False
''')]

DEFECTS = {
    "M01_retry_place": D01_RETRY_PLACE,
    "M02_turn_stamp": D02_TURN_STAMP,
    "M03_window_edge": D03_WINDOW_EDGE,
    "M04_ttl_retry_edge": D04_TTL_RETRY_EDGE,
    "M05_busy_units": D05_BUSY_UNITS,
    "M06_kib_scale": D06_KIB_SCALE,
    "M07_batch_capacity": D07_BATCH_CAPACITY,
    "M08_direct_reset": D08_DIRECT_RESET,
    "M09_reassembly_dup": D09_REASSEMBLY_DUP,
    "M10_dedup_rejected": D10_DEDUP_REJECTED,
    "M11_money_total": D11_MONEY_TOTAL,
    "M12_direct_limits": D12_DIRECT_LIMITS,
}

# ---------------------------------------------------------------- partial / local fixes
# Plausible local patches of the two shared-helper defects: they fix the
# visible caller and leave the helper (and its other callers) as they are.
LOCAL_DEDUP_EDGE = [("dedup.py", '''        if timewin.within(accepted_at, now, window_ms):
            return msg_id
''', '''        if timewin.within(accepted_at, now, window_ms) and now - accepted_at != window_ms:
            return msg_id
''')]
LOCAL_INVOICE_TOTAL = [("report.py", '''    out.append("total=%s lines=%d" % (money.fmt(money.total([l.amount for l in lines])),
                                      len(lines)))
''', '''    out.append("total=%s lines=%d" % (money.fmt(sum(l.cents() for l in lines)),
                                      len(lines)))
''')]

# ---------------------------------------------------------------- over-aggressive edits
# (e1) "urgent must respect quiet hours too" and "a duplicate refreshes the
# window": both change documented behaviour.
OA_QUIET_URGENT = [("dispatch.py", '''        if msg.prio != "urgent" and localtime.in_quiet(t, offset, cfg.quiet(r)):
''', '''        if localtime.in_quiet(t, offset, cfg.quiet(r)):
''')]
OA_DEDUP_REFRESH = [("intake.py", '''    if earlier is not None:
        svc.stats.bump("duplicates")
''', '''    if earlier is not None:
        svc.dedup.remember(key, now, earlier)
        svc.stats.bump("duplicates")
''')]
# (e2) money rounding "unified" on Python's round() (half to even).
OA_ROUNDING = [("money.py", '''    num, den = amount.numerator, amount.denominator
    return (2 * num + den) // (2 * den)
''', '''    return round(amount)
''')]
# (e3) limits applied to every fragment, also of messages that started.
OA_LIMITS_ALWAYS = [("dispatch.py", '''        if not msg.started and svc.limits.block_reason(cfg, r, offset, t, msg.size):
''', '''        if svc.limits.block_reason(cfg, r, offset, t, 0 if msg.started else msg.size):
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


def without(*names):
    return flat(*(edits for name, edits in DEFECTS.items() if name not in names))


def main():
    make_tree(os.path.join(TASK, "public", "src"), flat(*DEFECTS.values()))
    mut = os.path.join(HERE, "mutants")
    if os.path.exists(mut):
        shutil.rmtree(mut)
    for name, edits in DEFECTS.items():
        make_tree(os.path.join(mut, name), edits)
    ctl = os.path.join(HERE, "controls")
    # (d) partial fix: everything except the two hardest variants (sender
    # turn stamp, retry keeps its place).
    make_tree(os.path.join(ctl, "d_partial", "patch"),
              flat(D01_RETRY_PLACE, D02_TURN_STAMP))
    # (d2) naive fix: the "visible" defects fixed (invariant exits, busy
    # units, KiB, batch capacity, direct-path limits), the two shared
    # helpers patched only at the visible caller, ordering/state defects left.
    make_tree(os.path.join(ctl, "d2_local_patches", "patch"),
              flat(D01_RETRY_PLACE, D02_TURN_STAMP, D04_TTL_RETRY_EDGE, D08_DIRECT_RESET,
                   D10_DEDUP_REJECTED, D03_WINDOW_EDGE, D11_MONEY_TOTAL,
                   LOCAL_DEDUP_EDGE, LOCAL_INVOICE_TOTAL))
    # (e) over-aggressive fixes on top of the full fix
    make_tree(os.path.join(ctl, "e1_overaggressive_quiet_dedup", "patch"),
              flat(OA_QUIET_URGENT, OA_DEDUP_REFRESH))
    make_tree(os.path.join(ctl, "e2_overaggressive_rounding", "patch"), OA_ROUNDING)
    make_tree(os.path.join(ctl, "e3_overaggressive_limits", "patch"), OA_LIMITS_ALWAYS)
    print("public/src, %d mutants and control trees written" % len(DEFECTS))


if __name__ == "__main__":
    main()
