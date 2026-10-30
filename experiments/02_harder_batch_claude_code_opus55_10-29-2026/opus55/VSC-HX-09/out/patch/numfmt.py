# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Number and duration formatting.  All figures are computed in integer
arithmetic so that the same inputs print the same text everywhere."""


def pct1(n, d):
    """N/D as a percentage with one decimal, rounded half up.  D > 0."""
    tenths = (n * 2000 + d) // (2 * d)
    return "%d.%d" % divmod(tenths, 10)


def avg_int(total, n):
    """TOTAL/N rounded half up to a whole number.  N > 0."""
    return (2 * total + n) // (2 * n)


def fmt_duration(seconds):
    """Compact duration: 0s, 45s, 5m, 2h05m, 1d03h, 1d00h00m10s."""
    if seconds <= 0:
        return "0s"
    parts = []
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    if days:
        parts.append("%dd" % days)
    if hours or (days and (minutes or secs)):
        parts.append("%02dh" % hours if parts else "%dh" % hours)
    if minutes or (parts and secs):
        parts.append("%02dm" % minutes if parts else "%dm" % minutes)
    if secs:
        parts.append("%02ds" % secs if parts else "%ds" % secs)
    return "".join(parts)


def plural(n, word):
    return "%d %s%s" % (n, word, "" if n == 1 else "s")
