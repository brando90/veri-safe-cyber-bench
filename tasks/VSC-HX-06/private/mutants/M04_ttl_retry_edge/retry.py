# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""What happens after a failed attempt (README, "Retries").

After the n-th failed attempt of a fragment (n >= 1) the next attempt is
due ``min(retry.base_ms * retry.factor ** (n - 1), retry.cap_s)`` later, or
later still when the link asked for it (busy hint).  ``retry.factor`` is at
most 10 and n at most 10 (config.KEYS), and the cap applies before the hint.
"""

RETRY = "retry"
FAIL = "fail"
EXPIRE = "expire"


class Decision:
    __slots__ = ("kind", "at")

    def __init__(self, kind, at=None):
        self.kind = kind
        self.at = at


def backoff_ms(cfg, attempts):
    """Delay after the ATTEMPTS-th failed attempt, in milliseconds."""
    base = cfg.ms("retry.base_ms")
    factor = cfg.get("retry.factor")
    cap = cfg.ms("retry.cap_s")
    return min(base * factor ** (attempts - 1), cap)


def decide(cfg, msg, frag, now, hint_ms=0):
    """Decision after a failed attempt of FRAG at NOW.

    * fragment out of attempts -> FAIL (the message fails);
    * next attempt would be at or after the message deadline -> EXPIRE now;
    * otherwise RETRY at the computed instant.
    """
    if frag.attempts >= cfg.get("retry.max_attempts", msg.recipient):
        return Decision(FAIL)
    at = now + max(backoff_ms(cfg, frag.attempts), hint_ms)
    if at > msg.deadline:
        return Decision(EXPIRE)
    return Decision(RETRY, at)


def schedule_text(cfg, attempts_max):
    """Human-readable backoff table used by ``config retry``."""
    out = []
    for n in range(1, attempts_max):
        out.append(backoff_ms(cfg, n))
    return out
