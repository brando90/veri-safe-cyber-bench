# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Proleptic Gregorian calendar arithmetic on day numbers.

Day 0 is 1970-01-01.  Years 1 to 9999 are supported.  Weeks begin on
Monday, which is weekday 0.
"""


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def days_in_month(y, m):
    if m == 2:
        return 29 if is_leap(y) else 28
    return 30 + ((m + (m >> 3)) & 1)


def valid(y, m, d):
    return 1 <= y <= 9999 and 1 <= m <= 12 and 1 <= d <= days_in_month(y, m)


def days_from_civil(y, m, d):
    y -= m <= 2
    era = y // 400
    yoe = y - era * 400
    doy = (153 * (m + (-3 if m > 2 else 9)) + 2) // 5 + d - 1
    doe = yoe * 365 + yoe // 4 - yoe // 100 + doy
    return era * 146097 + doe - 719468


def civil_from_days(z):
    z += 719468
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + (3 if mp < 10 else -9)
    return y + (m <= 2), m, d


MIN_DAY = days_from_civil(1, 1, 1)
MAX_DAY = days_from_civil(9999, 12, 31)


def in_range(z):
    return MIN_DAY <= z <= MAX_DAY


def weekday(z):
    return (z + 3) % 7


def week_start(z):
    return z - weekday(z)


def weekday_name(z):
    return ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[weekday(z)]
