# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Version 1 calendar helpers, kept for reference.  Nothing imports this module."""

MONTH_STARTS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def day_of_year(y, m, d):
    leap = y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)
    return MONTH_STARTS[m - 1] + d + (1 if leap and m > 2 else 0)


def days_since_1970(y, m, d):
    days = (y - 1970) * 365
    days += (y - 1969) // 4 - (y - 1901) // 100 + (y - 1601) // 400
    return days + day_of_year(y, m, d) - 1


def v1_duration(text):
    total = 0
    for part in text.replace("h", "h ").replace("m", "m ").split():
        total += int(part[:-1]) * {"h": 3600, "m": 60}[part[-1]]
    return total
