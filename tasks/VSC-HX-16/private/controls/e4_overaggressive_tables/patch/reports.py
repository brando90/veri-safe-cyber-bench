# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The report command: counts, shares, alerts and future-dated records."""
import names
import stamp
import windows
from records import domain_of

ROW = "  %-14s %5d %6s%%"
LEVELS = ("error", "warn", "info", "debug")
DEFAULT_LEVEL = "info"


def ranked(counts):
    """Rows (name, count) in report order."""
    return sorted(counts.items(), key=lambda row: (-row[1], row[0]))


def share(part, whole):
    """PART as a percentage of WHOLE, as text."""
    if whole == 0:
        return "0.0"
    tenths = (part * 2000 + whole) // (2 * whole)
    return "%d.%d" % divmod(tenths, 10)


def table(title, counts, total, limit=None):
    lines = [title]
    rows = ranked(counts)
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        lines.append("  none")
    for name, count in rows:
        lines.append(ROW % (name, count, share(count, total)))
    return lines


def level_rank(level):
    try:
        return LEVELS.index(level)
    except ValueError:
        return len(LEVELS)


def level_table(records, total):
    counts = tally(r.fields.get("level", DEFAULT_LEVEL).lower() for r in records)
    lines = ["by level:"]
    if not counts:
        lines.append("  none")
    for level, count in sorted(counts.items()):
        lines.append(ROW % (level, count, share(count, total)))
    return lines


def tally(values):
    counts = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def build(world):
    records = world.store.records
    total = len(records)
    lines = ["report at %s" % stamp.fmt(world.now)]
    lines.append("records: %d (bytes %d)" % (total, sum(r.size for r in records)))
    per_source = tally(r.source for r in records)
    if per_source:
        lines.append("sources: %d, average %d records per source" % (
            len(per_source), round(total / len(per_source))))
    else:
        lines.append("sources: 0")
    lines.extend(table("by source:", per_source, total))
    lines.extend(table("by user (top %d):" % world.top, tally(r.user for r in records),
                       total, world.top))
    lines.extend(table("by domain:", tally(domain_of(r.user) for r in records), total))
    lines.extend(level_table(records, total))
    if records:
        biggest = max(records, key=lambda r: r.size)
        lines.append("largest record: #%d (%d bytes)" % (biggest.id, biggest.size))
    found = windows.alerts(records, world.window, world.limit_for)
    lines.append("alerts (window %ds):" % world.window)
    if not found:
        lines.append("  none")
    for source, top, limit in found:
        lines.append("  ALERT %s peak %d limit %d" % (source, top, limit))
    for source in windows.at_limit(records, world.window, world.limit_for):
        lines.append("  at limit %s" % source)
    ahead = [(r.id, stamp.days_ahead(world.now, r.when)) for r in records]
    ahead = [(rid, days) for rid, days in ahead if days > 0]
    if ahead:
        lines.append("future:")
        for rid, days in ahead:
            lines.append("  #%d is %d day%s ahead" % (rid, days, "" if days == 1 else "s"))
    return lines


def days(world):
    """One line per UTC day that has records, oldest day first."""
    buckets = {}
    for record in world.store.records:
        count, size = buckets.get(stamp.day_of(record.when), (0, 0))
        buckets[stamp.day_of(record.when)] = (count + 1, size + record.size)
    if not buckets:
        return ["no records"]
    return ["%s %4d records, bytes %d" % (day, buckets[day][0], buckets[day][1])
            for day in sorted(buckets)]


def field_stats(world):
    """How many records carry each field, counted by normalised name."""
    records = world.store.records
    counts = tally(n for r in records for n in sorted({names.base(f) for f in r.fields}))
    lines = ["fields:"]
    lines.extend(table("", counts, len(records))[1:])
    return lines
