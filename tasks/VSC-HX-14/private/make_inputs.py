#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write every .in file of public/smoke, private/ref_tests and private/ref_edge.

Hand-written cases are listed below; the generated sessions come from a
stateful generator that runs each command through the gold tree while it
builds the session (so it can pick real occurrences to skip and so on).  The
generator has a set of "hazards": shapes that reach a defect.  With no
hazard it produces only ordinary shapes (used by ref_tests and, as a check,
every mutant must pass those sessions with the gold output).  Fixed seeds.
The expected .out files are made by build_private.sh from the gold tree.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
GOLD = os.path.join(HERE, "gold")
sys.path.insert(0, GOLD)
sys.dont_write_bytecode = True

import checksum  # noqa: E402
import civil  # noqa: E402
import events  # noqa: E402
import expand  # noqa: E402
import ids  # noqa: E402
import lexer  # noqa: E402
import pack  # noqa: E402
import rules  # noqa: E402
import timeparse  # noqa: E402
import durations  # noqa: E402
import offsets  # noqa: E402
import fields  # noqa: E402
import textrec  # noqa: E402
from errors import CommandError, InvariantViolation  # noqa: E402
from world import World  # noqa: E402
import invariant  # noqa: E402


class NullOut:
    def emit(self, line):
        pass


# ---------------------------------------------------------------- generator
WORDS = ["Standup", "Review", "Sync", "Planning", "Retro", "Lunch", "Demo", "Workshop", "Call",
         "Interview", "Training", "Checkin", "Budget", "Roadmap", "Office hours"]
CATS = ["work", "team", "social", "health", "travel", "ops", "deep focus"]
TZS = ["Z", "+01:00", "+05:30", "-05:00", "-08:00", "+09:00", "-03:30", "+02:00", "+12:45",
       "-04:00", "+0530", "+10"]
DURS = ["15m", "30m", "45m", "1h", "90m", "2h", "1h30m", "3h", "45s", "1.5h", "0.25h", "1d"]
WD = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
HAZARDS = ("civil", "cats", "varint", "offset", "weekly", "snap", "natural", "ref", "move", "title")


class Gen:
    def __init__(self, seed, hazards=(), max_events=60, hazard_rate=0.25):
        self.rng = random.Random(seed)
        self.hazards = set(hazards)
        self.max_events = max_events
        self.rate = hazard_rate
        self.world = World(NullOut())
        self.lines = []
        self.counter = 0

    # -- running a command in the gold tree while generating it
    def run(self, line):
        self.lines.append(line)
        try:
            cmd = lexer.parse(line)
            if cmd is None:
                return True
            self.world.dispatch(cmd)
            invariant.full_check(self.world)
            return True
        except CommandError:
            return False
        except InvariantViolation as exc:  # the generator must never break gold
            raise AssertionError("gold failed on %r: %s" % (line, exc))

    def hz(self, name):
        return name in self.hazards and self.rng.random() < self.rate

    # -- pieces
    def date(self, lo=2023, hi=2026):
        y = self.rng.randint(lo, hi)
        m = self.rng.randint(1, 12)
        d = self.rng.randint(1, civil.days_in_month(y, m))
        return y, m, d

    def start_text(self, allday=False):
        y, m, d = self.date()
        if self.hz("civil"):
            y, m, d = self.rng.choice([(2000, 2, 29), (2400, 2, 29), (1600, 2, 29)])
        if allday:
            return "%04d-%02d-%02d" % (y, m, d)
        h = self.rng.randint(6, 21)
        mi = self.rng.randrange(0, 60, 5)
        text = "%04d-%02d-%02dT%02d:%02d" % (y, m, d, h, mi)
        if self.rng.random() < 0.15:
            text += ":%02d" % self.rng.choice([0, 5, 29, 30, 45, 59])
            if h == 23 and mi == 59:
                text = text[:-3]
        if self.hz("snap"):
            text = "%04d-%02d-%02dT23:59:%02d" % (y, m, d, self.rng.randint(30, 59))
        if self.hz("varint"):
            text = "%04d-%02d-%02dT02:08" % (y, m, d)
        return text

    def tz(self):
        if self.hz("offset"):
            return self.rng.choice(["-00:30", "-00:45", "-00:15", "-0030", "-00:59"])
        return self.rng.choice(TZS)

    def dur(self):
        if self.hz("varint"):
            return self.rng.choice(["2m8s", "128s", "4h34m", "4h33m10s", "24d7h", "24d6h40m"])
        return self.rng.choice(DURS)

    def title(self):
        t = self.rng.choice(WORDS)
        if self.rng.random() < 0.3:
            t += " " + self.rng.choice(["A", "B", "q3", "x"])
        if self.rng.random() < 0.08:
            t = t.replace(" ", "  ")
        if self.hz("title"):
            t = t.replace(" ", " " * self.rng.choice([3, 4, 6]))
            if " " not in t:
                t += "   end"
        return t

    def cats(self):
        picks = self.rng.sample(CATS, self.rng.randint(0, 3))
        if self.hz("cats"):
            picks.append(self.rng.choice(["back\\\\slash", "tail\\\\", "a\\\\,b", "x\\,y"]))
        return ",".join(picks)

    def rule(self, start_text, safe_moves=True):
        r = self.rng
        roll = r.random()
        if roll < 0.35:
            return None
        day = timeparse.parse_date(start_text[:10])
        wd0 = civil.weekday(day)
        tail = ""
        if r.random() < 0.3:
            tail = ";count=%d" % r.randint(2, 9)
        elif r.random() < 0.15:
            tail = ";until=%s" % timeparse.format_date(day + r.randint(20, 400))
        kind = r.choice(["daily", "weekly", "weekly", "monthly", "monthly", "yearly"])
        every = r.choice([1, 1, 2, 3])
        ev = "" if every == 1 else ";every=%d" % every
        if kind == "daily":
            return "daily" + ev + tail
        if kind == "weekly":
            if every > 1 and wd0 > 0 and self.hz("weekly"):
                days = set(r.sample(range(wd0), r.randint(1, min(2, wd0))))
                days |= set(r.sample(range(wd0, 7), min(r.randint(0, 2), 7 - wd0)))
            elif every > 1:
                days = set(r.sample(range(wd0, 7), r.randint(1, min(3, 7 - wd0))))
            else:
                days = set(r.sample(range(7), r.randint(1, 3)))
            on = ",".join(WD[i] for i in sorted(days))
            return "weekly%s;on=%s%s" % (ev, on, tail)
        if kind == "monthly":
            if r.random() < 0.5:
                return "monthly%s;monthday=%d%s" % (ev, r.choice([1, 15, 28, 29, 30, 31]), tail)
            return "monthly%s;on=%s%s" % (ev, ",".join(
                "%d%s" % (r.choice([1, 2, 3, -1]), WD[r.randrange(7)]) for _ in range(r.randint(1, 2))),
                tail)
        return "yearly" + ev + tail

    def new_id(self):
        self.counter += 1
        return "ev%d" % self.counter if self.rng.random() < 0.8 else "-"

    def tie_group(self):
        """Events with the same start and priority and ids that differ after the second chunk."""
        r = self.rng
        stem = r.choice(["r%d" % r.randint(1, 9), "room%d" % r.randint(1, 9), "ev-%d" % r.randint(1, 9)])
        tails = r.choice([["d10", "d9", "d100", "d9b"], ["-z", "-a", "-a2", "-a10"], ["x2y", "x10y", "x1y"]])
        r.shuffle(tails)
        start = self.start_text().replace("T02:08", "T09:00")
        prio = r.randint(0, 9)
        for tail in tails:
            self.counter += 1
            self.run('event add %s%s "Tie %d" %s prio=%d' % (stem, tail, self.counter, start, prio))

    def move_group(self):
        """A recurring event with skips, then moved to another weekday."""
        r = self.rng
        self.counter += 1
        eid = "ev%d" % self.counter
        start = self.start_text()
        freq = r.choice(["weekly", "weekly", "monthly", "yearly"])
        self.run('event add %s "Moving" %s rule=%s' % (eid, start, freq))
        ev = self.world.store.by_id.get(eid)
        if ev is None:
            return
        for d in r.sample(expand.first(ev, 6, with_skips=True), 2):
            self.run("skip %s %s" % (eid, timeparse.format_date(d)))
        day = ev.start // 86400 + r.randint(1, 3)
        self.run("event move %s %sT%02d:00" % (eid, timeparse.format_date(day), r.randint(6, 20)))
        self.run("event show %s" % eid)

    def add(self):
        allday = self.rng.random() < 0.1
        start = self.start_text(allday)
        opts = []
        if self.rng.random() < 0.8:
            opts.append("dur=%s" % self.dur())
        rule = None if allday and self.rng.random() < 0.5 else self.rule(start)
        if rule:
            opts.append("rule=%s" % rule)
        if self.rng.random() < 0.7:
            opts.append("tz=%s" % self.tz())
        if allday:
            opts.append("allday=yes")
        if self.rng.random() < 0.6:
            opts.append("prio=%d" % self.rng.randint(0, 9))
        cats = self.cats()
        if cats:
            opts.append("cat=%s" % cats)
        self.run('event add %s "%s" %s %s' % (self.new_id(), self.title(), start, " ".join(opts)))

    def created(self):
        return self.world.store.next_seq - 1

    def pick(self):
        evs = self.world.store.ordered()
        return self.rng.choice(evs) if evs else None

    def window(self, span, around=None):
        if around is None:
            y, m, d = self.date()
            around = civil.days_from_civil(y, m, d)
        lo = around - self.rng.randint(0, 10)
        return timeparse.format_date(lo), timeparse.format_date(lo + span)

    def step(self):
        r = self.rng
        n = len(self.world.store.by_id)
        roll = r.random()
        if self.hz("natural") and roll < 0.1:
            return self.tie_group()
        if self.hz("move") and roll < 0.1:
            return self.move_group()
        if n < 3 or (roll < 0.30 and n < self.max_events and self.created() < 110):
            return self.add()
        ev = self.pick()
        if ev is None:
            return self.add()
        ref = ev.id if r.random() < 0.8 else "#" + ids.encode(ev.seq)
        day = ev.start // 86400
        if roll < 0.38:
            self.run("event show %s" % ref)
        elif roll < 0.50:
            lo, hi = self.window(r.choice([14, 40, 120]), day)
            self.run("expand %s %s %s" % (ref, lo, hi))
        elif roll < 0.60:
            lo, hi = self.window(r.choice([3, 6, 13]), day)
            self.run("agenda %s %s%s" % (lo, hi, " n=5" if r.random() < 0.3 else ""))
        elif roll < 0.64:
            lo, hi = self.window(r.choice([3, 6, 20]), day)
            self.run("busy %s %s" % (lo, hi))
        elif roll < 0.74 and ev.rule:
            days = expand.first(ev, 6, with_skips=True)
            if days:
                self.run("skip %s %s" % (ref, timeparse.format_date(r.choice(days))))
        elif roll < 0.77 and ev.skips:
            self.run("unskip %s %s" % (ref, timeparse.format_date(r.choice(ev.skips))))
        elif roll < 0.82:
            self.move(ev, ref)
        elif roll < 0.85:
            text = self.rule(timeparse.format_instant(ev.start))
            self.run("event rule %s %s" % (ref, text or "none"))
        elif roll < 0.88:
            self.run('event retitle %s "%s"' % (ref, self.title()))
        elif roll < 0.90:
            self.run("event cat %s %s" % (ref, self.cats() or "-"))
        elif roll < 0.92:
            self.run("event set %s prio=%d tz=%s" % (ref, r.randint(0, 9), self.tz()))
        elif roll < 0.93 and n > 8:
            self.run("event rm %s" % ref)
        elif roll < 0.95:
            self.run(r.choice(["list", "stats", "check", "export text"]))
        else:
            self.tool()

    def move(self, ev, ref):
        weekly_step = ev.rule is not None and ev.rule.freq == "weekly" and ev.rule.every > 1
        safe = not ev.skips and not weekly_step
        if not safe and not ("weekly" in self.hazards and not ev.skips):
            return
        self.run("event move %s %s" % (ref, self.start_text(ev.allday)))

    def tool(self):
        r = self.rng
        y, m, d = self.date()
        date = "%04d-%02d-%02d" % (y, m, d)
        self.run(r.choice([
            "ordinal " + date, "weekday " + date, "shift %s %d %s" % (
                date, r.randint(-14, 14), r.choice(["days", "weeks", "months", "years"])),
            "offset " + self.tz(), "dur " + self.dur(), "snap %sT%02d:%02d:%02d" % (
                date, r.randint(0, 22), r.randint(0, 59), r.randint(0, 59)),
            "title \"%s\"" % self.title(), "ref %d" % r.randint(0, 5000),
            "unref %s" % ids.encode(r.randint(0, 5000)), "date %d" % r.choice(
                [n for n in (r.randint(0, 25000), r.randint(0, 25000)) if n != 11016] or [5])]))

    def session(self, n):
        while len(self.lines) < n:
            self.step()
        if "ref" in self.hazards:
            self.run("idseq %d" % (ids.MAX_SEQ - r_choice(self.rng, [0, 1, 2])))
            self.run('event add - "Last one" 2024-05-05T10:00')
            self.run("list")
        self.run("check")
        return self.lines


def r_choice(rng, seq):
    return rng.choice(seq)


# ---------------------------------------------------------------- hand-written cases
def write(directory, name, lines):
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, name + ".in"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def mk(eid, seq, title, start, dur="1h", rule=None, tz="Z", allday=False, prio=5, cats=(),
       skips=()):
    """An Event built the way the commands build it (for records and frames)."""
    st, raw = timeparse.parse_start(start, allday)
    return events.Event(eid, seq, title, st, raw, durations.parse(dur),
                        rules.parse(rule) if rule else None, offsets.parse(tz), allday, prio,
                        list(cats), [timeparse.parse_date(d) for d in skips])


def rec(*args, **kw):
    return textrec.format_record(mk(*args, **kw))


def pack_input(evs, total_override=None):
    data, total = pack.frame(evs)
    if total_override is not None:
        total = total_override
    return "import pack %04x %s" % (total, data.hex())


SMOKE = {
    "s1_basic_events": [
        "# add a few events and look at them",
        'event add standup "Team standup" 2024-03-04T09:30 dur=15m rule=weekly;on=MO,TU,WE,TH,FR prio=6 cat=work',
        'event add - "Dentist" 2024-03-12T14:00 dur=45m tz=+01:00',
        'event add review "Quarterly review" 2024-03-15T10:00 dur=2h rule=monthly;monthday=15 cat=work,planning',
        "list",
        "event show standup",
        "event show #2",
        "expand standup 2024-03-04 2024-03-15",
        "stats",
    ],
    "s2_agenda_busy": [
        'event add a1 "Design sync" 2024-05-06T09:00 dur=1h prio=5',
        'event add a2 "Customer call" 2024-05-06T09:30 dur=1h tz=+02:00 prio=8',
        'event add a3 "Planning" 2024-05-06T10:00 dur=30m prio=5',
        'event add a4 "Demo" 2024-05-07T15:00 dur=1h tz=-05:00',
        "agenda 2024-05-06 2024-05-07",
        "busy 2024-05-06 2024-05-07",
        "agenda 2024-05-06 2024-05-07 n=2",
    ],
    "s3_skips_and_rules": [
        'event add gym "Gym" 2024-06-03T07:00 dur=1h rule=weekly;on=MO,WE,FR;count=8',
        "skip gym 2024-06-05",
        "skip gym 2024-06-06",
        "expand gym 2024-06-01 2024-06-30",
        "unskip gym 2024-06-05",
        "event rule gym weekly;on=MO",
        "event show gym",
        "rule Monthly;ON=2tu,-1fr;COUNT=5",
    ],
    "s4_conversions": [
        "ordinal 2024-03-01",
        "date 19783",
        "weekday 2024-12-25",
        "shift 2024-01-31 1 month",
        "shift 2024-03-15 -2 weeks",
        "offset +0530",
        "dur 1h30m",
        "dur 1.5h",
        "snap 2024-03-04T10:15:40",
        "ref 1000",
        "unref 1s8",
        'title "  weekly  review "',
    ],
    "s5_export_import_errors": [
        'event add x1 "Export me" 2024-07-01T08:00 dur=30m cat=a,b prio=3',
        "export text",
        "export pack",
        "import rec \"%s\"" % rec("x2", 2, "Imported", "2024-07-02T08:00"),
        "list",
        "event show nosuch",
        "event add x1 \"Again\" 2024-07-03T08:00",
        "skip x2 2024-07-02",
        "expand x1 2024-07-05 2024-07-01",
        "check",
    ],
}


def ref_tests():
    t = {}
    t["t01_daily_every_count"] = [
        'event add d1 "Pill" 2024-02-27T08:00 dur=5m rule=daily;every=2;count=6',
        "expand d1 2024-02-01 2024-03-31",
        'event add d2 "Water" 2024-02-27T09:00 dur=5m rule=daily;until=2024-03-02',
        "expand d2 2024-02-01 2024-03-31",
        "event show d1",
    ]
    t["t02_weekly_from_monday"] = [
        'event add w1 "Sprint" 2024-03-04T10:00 rule=weekly;every=2;on=MO,WE,FR',
        "expand w1 2024-03-01 2024-04-30",
        'event add w2 "Long cycle" 2024-03-04T11:00 rule=weekly;every=3;on=TU',
        "expand w2 2024-03-01 2024-06-30",
        "check",
    ]
    t["t03_weekly_default_day"] = [
        'event add w1 "Thursday thing" 2024-03-07T10:00 rule=weekly;every=2',
        "expand w1 2024-03-01 2024-05-15",
        'event add w2 "Starts on Sunday" 2024-03-10T10:00 rule=weekly;on=SU,MO',
        "expand w2 2024-03-01 2024-04-15",
    ]
    t["t04_monthly_month_end"] = [
        'event add m1 "Payday" 2024-01-31T09:00 rule=monthly',
        "expand m1 2024-01-01 2024-12-31",
        'event add m2 "Rent" 2024-01-30T09:00 rule=monthly;monthday=31;every=2',
        "expand m2 2024-01-01 2025-03-31",
        'event add m3 "Early" 2024-01-20T09:00 rule=monthly;monthday=10;count=3',
        "expand m3 2024-01-01 2024-12-31",
    ]
    t["t05_monthly_positioned"] = [
        'event add p1 "Board" 2024-03-01T16:00 rule=monthly;on=2TU,-1FR',
        "expand p1 2024-03-01 2024-08-31",
        'event add p2 "Fifth" 2024-01-01T16:00 rule=monthly;on=5MO',
        "expand p2 2024-01-01 2024-12-31",
        'event add p3 "Last Sunday" 2024-01-01T16:00 rule=monthly;on=-1SU;every=3;count=4',
        "expand p3 2024-01-01 2025-12-31",
    ]
    t["t06_yearly_leap_day"] = [
        'event add y1 "Leap" 2024-02-29T12:00 rule=yearly',
        "expand y1 2024-01-01 2029-12-31",
        'event add y2 "Anniversary" 2023-11-05T12:00 rule=yearly;every=2;count=4',
        "expand y2 2023-01-01 2035-12-31",
    ]
    t["t07_count_includes_skips"] = [
        'event add c1 "Course" 2024-04-01T18:00 rule=daily;count=5',
        "skip c1 2024-04-02",
        "skip c1 2024-04-04",
        "expand c1 2024-04-01 2024-04-30",
        "event show c1",
        "unskip c1 2024-04-02",
        "expand c1 2024-04-01 2024-04-30",
    ]
    t["t08_agenda_priority_ties"] = [
        'event add ev1 "Low" 2024-05-06T09:00 prio=2',
        'event add ev2 "High" 2024-05-06T09:00 prio=9',
        'event add ev9 "Nine" 2024-05-06T09:00 prio=5',
        'event add ev10 "Ten" 2024-05-06T09:00 prio=5',
        'event add ev11 "Eleven" 2024-05-06T09:00 prio=5',
        'event add ev100 "Hundred" 2024-05-06T09:00 prio=5',
        'event add ev2a "Two a" 2024-05-06T09:00 prio=5',
        "agenda 2024-05-06 2024-05-06",
        "agenda 2024-05-06 2024-05-06 n=3",
    ]
    t["t09_agenda_zones"] = [
        'event add z1 "Berlin" 2024-05-06T01:30 tz=+02:00',
        'event add z2 "New York" 2024-05-05T21:30 tz=-04:00',
        'event add z3 "Delhi" 2024-05-06T07:00 tz=+05:30 prio=1',
        'event add z4 "Floating" 2024-05-06 allday=yes tz=+09:00',
        "agenda 2024-05-05 2024-05-06",
        "agenda 2024-05-06 2024-05-06",
        "busy 2024-05-05 2024-05-06",
    ]
    t["t10_busy_touching"] = [
        'event add b1 "One" 2024-05-06T09:00 dur=1h',
        'event add b2 "Two" 2024-05-06T10:00 dur=30m',
        'event add b3 "Three" 2024-05-06T10:15 dur=2h',
        'event add b4 "Four" 2024-05-06T14:00 dur=1h',
        'event add b5 "Five" 2024-05-07T08:00 dur=90m rule=daily;count=3',
        "busy 2024-05-06 2024-05-09",
        "busy 2024-05-07 2024-05-07",
    ]
    t["t11_shift_chains"] = [
        "shift 2024-01-31 1 month",
        "shift 2024-02-29 1 month",
        "shift 2024-02-29 1 year",
        "shift 2024-02-29 4 years",
        "shift 2024-03-31 -1 month",
        "shift 2024-03-31 -13 months",
        "shift 2023-12-31 2 months",
        "shift 2024-12-25 10 weeks",
        "shift 2024-12-25 -400 days",
        "shift 9999-12-31 1 day",
        "shift 0001-01-01 -1 day",
        "shift 2024-01-01 1 fortnight",
        "shift 2024-01-01 x days",
    ]
    t["t12_durations"] = [
        "dur 1h30m", "dur 90m", "dur 0s", "dur 1d2h3m4s", "dur 36h", "dur 1.5h", "dur 0.375m",
        "dur 0.00125h", "dur 0.5s", "dur 0.4s", "dur 2.5d", "dur 400d", "dur 400d1s",
        "dur 1m2h", "dur 2h2h", "dur 1.5h30m", "dur h", "dur 1.1234567h", "dur 61m",
    ]
    t["t13_offsets"] = [
        "offset Z", "offset +00:00", "offset -00:00", "offset +0530", "offset +05", "offset -03:30",
        "offset -12:00", "offset +14:00", "offset +14:30", "offset -12:30", "offset +05:60",
        "offset 5:30", "offset +5", "offset +1230", "offset -0800",
        'event add o1 "Offset" 2024-01-01T10:00 tz=+05:45',
        "event show o1",
    ]
    t["t14_titles"] = [
        'title "  plain  words here  "',
        'title "tab\tseparated\t\twords"',
        'title "a  b"',
        'title "non breaking  space stays"',
        'title "café  crème"',
        'title ""',
        'title "back\\slash and | bar"',
        'event add t1 "  Weekly  sync  " 2024-03-04T10:00',
        'event add t2 "Pipe | and \\ slash" 2024-03-04T11:00',
        'event retitle t1 "Renamed  twice"',
        "event show t1",
        "event show t2",
        "export text",
    ]
    t["t15_text_records"] = [
        'event add r1 "First" 2024-03-04T10:00 dur=90m rule=weekly;on=MO,TH tz=+05:30 prio=7 cat=a,b',
        "skip r1 2024-03-07",
        "export text",
        "import rec \"%s\"" % rec("r2", 40, "Second", "2024-04-01T09:00"),
        "import rec \"%s\"" % rec("r3", 41, "Third | pipe", "2024-04-02", dur="1d", allday=True,
                                  cats=["x,y", "z"]),
        'import rec "E|r4|42|Bad|2024-04-02T10:00|0|1h||+00:00||5||"',
        'import rec "E|r1|43|Dup|2024-04-02T10:00|1712052000|1h||+00:00||5||"',
        'import rec "garbage"',
        "export text",
        "event show r3",
        "event add - \"after import\" 2024-04-05T10:00",
        "list",
    ]
    fresh = [
        mk("n1", 50, "Packed one", "2024-06-10T09:00", dur="30m", rule="weekly;on=MO,FR", tz="+02:00",
           prio=4, cats=["x", "y"], skips=["2024-06-14"]),
        mk("n2", 51, "Packed two", "2024-06-11", dur="1d", allday=True, prio=9),
    ]
    t["t16_pack_roundtrip"] = [
        'event add p0 "Existing" 2024-06-01T10:00',
        "export pack",
        pack_input(fresh),
        "list",
        "event show n1",
        "export pack",
        pack_input(fresh, total_override=0x1234),
        "import pack zz 00",
        "import pack 0000 0xzz",
        "import pack 0000 00",
        "check",
    ]
    t["t17_references"] = [
        "ref 0", "ref 31", "ref 32", "ref 1023", "ref 1024", "ref 32767", "ref 32768",
        "ref 1048576", "ref 1099511627776", "unref 10", "unref zz", "unref ILO", "unref o", "unref",
        "unref 11111111111", "unref 1u", "ref -1", "ref 1125899906842624", "ref x",
        "idseq 31",
        'event add - "thirty one" 2024-03-04T10:00',
        'event add - "thirty two" 2024-03-04T11:00',
        'event add - "thirty three" 2024-03-04T12:00',
        "list",
        "event show #1Z",
        "event show #10",
        "event show #1o",
        "event show #",
        "idseq 5",
        "idseq 99999999999999999",
    ]
    t["t18_skip_pruning_by_rule"] = [
        'event add s1 "Series" 2024-03-04T10:00 rule=daily;count=10',
        "skip s1 2024-03-05",
        "skip s1 2024-03-08",
        "skip s1 2024-03-06",
        "skip s1 2024-03-20",
        "skip s1 2024-03-05",
        "event show s1",
        "event rule s1 weekly;on=MO,TU;count=6",
        "event show s1",
        "event rule s1 none",
        "event show s1",
        "skip s1 2024-03-04",
        "unskip s1 2024-03-04",
        "unskip s1 2024-03-04",
    ]
    t["t19_move_keeps_valid_skips"] = [
        'event add mv "Every day" 2024-03-04T10:00 rule=daily',
        "skip mv 2024-03-10",
        "skip mv 2024-03-12",
        "event move mv 2024-03-06T08:30",
        "event show mv",
        'event add mw "Weekly" 2024-03-18T10:00 rule=weekly',
        "skip mw 2024-03-25",
        "event move mw 2024-03-11T09:00",
        "event show mw",
        "expand mw 2024-03-01 2024-04-30",
    ]
    t["t20_allday_floating"] = [
        'event add h1 "Holiday" 2024-12-24 allday=yes tz=-08:00 rule=yearly',
        'event add h2 "Offsite" 2024-03-04 allday=yes dur=3d tz=+13:00 prio=7',
        "event show h1",
        "agenda 2024-03-03 2024-03-05",
        "busy 2024-03-03 2024-03-08",
        "expand h1 2024-01-01 2026-12-31",
        'event add h3 "Bad" 2024-03-04T10:00 allday=yes',
        'event add h4 "Bad" 2024-03-04 allday=maybe',
        "event move h2 2024-03-05T10:00",
        "event move h2 2024-03-06",
        "list",
    ]
    t["t21_snap_half_up"] = [
        "snap 2024-03-04T10:30:00",
        "snap 2024-03-04T10:30:29",
        "snap 2024-03-04T10:30:30",
        "snap 2024-03-04T10:59:30",
        "snap 2024-03-04T11:59:45",
        "snap 2024-03-04T00:00:59",
        "snap 2024-03-04T12:00:60",
        "snap 2024-02-30T10:00",
        "snap 2024-03-04T24:00",
        "snap 9999-12-31T23:59:29",
        'event add q1 "Seconds" 2024-03-04T10:30:45',
        "event show q1",
        'event add q2 "Seconds all" 2024-03-04T12:59:30 tz=+01:00',
        "event show q2",
    ]
    t["t22_error_messages"] = [
        "bogus", "event", "event add", "event add 1x \"t\" 2024-01-01T10:00",
        'event add e1 "t" 2024-01-01', 'event add e1 "t" 2024-13-01T10:00',
        'event add e1 "t" 2024-01-01T10:00 dur=x', 'event add e1 "t" 2024-01-01T10:00 tz=+15:00',
        'event add e1 "t" 2024-01-01T10:00 prio=10', 'event add e1 "t" 2024-01-01T10:00 colour=red',
        'event add e1 "t" 2024-01-01T10:00 rule=hourly',
        'event add e1 "t" 2024-01-01T10:00 rule=weekly;on=2MO',
        'event add e1 "t" 2024-01-01T10:00 rule=monthly;on=MO',
        'event add e1 "t" 2024-01-01T10:00 rule=monthly;monthday=3;on=1MO',
        'event add e1 "t" 2024-01-01T10:00 rule=daily;every=0',
        'event add e1 "t" 2024-01-01T10:00 cat=a,,b',
        'event add e1 "t" 2024-01-01T10:00 allday=yes',
        'event add "unclosed 2024-01-01T10:00',
        'event add e2 "ok" 2024-01-01T10:00',
        'event add e2 "again" 2024-01-01T10:00',
        "skip e2 2024-01-01", "expand e2 2024-01-02 2024-01-01", "expand e2 2020-01-01 2030-01-01",
        "expand nosuch 2024-01-01 2024-01-02", "agenda 2024-01-01 2025-06-01", "busy 2024-01-02 2024-01-01",
        "event show #zz!", "event show #7", "help event add", "help nosuch",
        "event add e3 \"a=b\" 2024-01-01T10:00",
    ]
    t["t23_stats_categories"] = [
        'event add c1 "One" 2024-01-01T10:00 cat=work,team',
        'event add c2 "Two" 2024-02-01T10:00 cat=work',
        'event add c3 "Three" 2024-03-01T10:00 cat=team,ops,work',
        'event add c4 "Four" 2024-04-01T10:00 cat=ops',
        'event add c5 "Five" 2024-05-01T10:00 cat=zeta,alpha',
        'event add c6 "Six" 2024-05-01T11:00 cat=zeta',
        "stats",
        "event cat c1 -",
        "event cat c3 a\\,b,a\\,b,c",
        "event show c3",
        "stats",
    ]
    t["t24_big_windows"] = [
        'event add big "Daily forever" 2020-01-01T06:00 dur=10m rule=daily',
        "expand big 2020-01-01 2029-12-31",
        "expand big 2030-01-01 2030-12-31",
        'event add far "Far" 2024-01-01T06:00 rule=daily',
        "expand far 2300-01-01 2300-01-05",
        'event add far2 "Far weekly" 2024-01-01T06:00 rule=weekly;every=52',
        "expand far2 2024-01-01 2030-12-31",
        "agenda 2024-01-01 2025-02-04",
        "agenda 2024-01-01 2024-12-31 n=3",
    ]
    # generated sessions with no hazard (every mutant must reproduce the gold output)
    t["t25_session_a"] = Gen(101, (), max_events=45).session(420)
    t["t26_session_b"] = Gen(202, (), max_events=60).session(700)
    t["t27_session_c"] = Gen(303, (), max_events=30).session(300)
    t["t28_long_ordinary"] = Gen(404, (), max_events=100).session(1500)
    return t


def ref_edge():
    e = {}
    # M01 -- day numbers at the end of a 400-year cycle
    e["e01_civil_leap_day_2000"] = [
        'event add a "Millennium leap day" 2000-02-29T10:00 rule=yearly;count=3',
        "event show a",
        "expand a 2000-01-01 2009-12-31",
        "date 11016",
        "ordinal 2000-02-29",
        "weekday 2000-02-29",
        "shift 2000-02-29 1 month",
        "shift 2000-02-28 1 day",
        "snap 2000-02-28T23:59:30",
    ]
    e["e02_civil_leap_days_other_cycles"] = [
        'event add b "Far future" 2400-02-29T08:00 dur=2h rule=daily;count=3',
        'event add c "Far past" 1600-02-29T08:00',
        "event show b",
        "event show c",
        "expand b 2400-02-27 2400-03-02",
        "date %d" % civil.days_from_civil(1600, 2, 29),
        "date %d" % civil.days_from_civil(2400, 2, 29),
        "date %d" % (civil.days_from_civil(2400, 2, 29) - 1),
        "date %d" % (civil.days_from_civil(2400, 2, 29) + 1),
        "ordinal 1600-02-29",
        "ordinal 2400-02-29",
        "export text",
        "check",
    ]
    # M02 -- backslash inside a category
    e["e03_category_backslash"] = [
        'event add a "Paths" 2024-03-04T10:00 cat=back\\\\slash,plain',
        'event add b "Trailing" 2024-03-04T11:00 cat=tail\\\\,next',
        "event show a",
        "event show b",
        "export text",
        "stats",
    ]
    e["e04_category_backslash_import_edit"] = [
        'event add a "Start" 2024-03-04T10:00 cat=x',
        'event cat a end\\\\',
        "event show a",
        'event cat a one\\,two,three\\\\\\,four',
        "event show a",
        "export text",
        "import rec \"%s\"" % rec("b", 9, "Imported", "2024-04-01T09:00", cats=["p\\q", "r\\,s"]),
        "event show b",
        "export text",
    ]
    # M03 -- base-128 integers that sit on a group boundary
    e["e05_varint_duration_values"] = [
        'event add a "Short" 2024-03-04T10:00 dur=2m8s',
        'event add b "Afternoon" 2024-03-04T11:00 dur=4h34m',
        'event add c "Long" 2024-03-05T11:00 dur=24d7h',
        "event show a",
        "event show b",
        "event show c",
        "export pack",
        "export text",
    ]
    e["e06_varint_clock_zone_skip_values"] = [
        'event add a "Early" 2024-03-04T02:08 rule=daily;count=300 tz=+01:04',
        "skip a 2024-03-04",
        "skip a 2024-07-10",
        "export pack",
        'event add b "Old" 1992-07-04T10:00',
        "export pack",
        pack_input([mk("n1", 90, "Imported long", "2024-06-10T09:00", dur="4h34m", rule="daily;count=5",
                       prio=4)]),
        "list",
    ]
    # M04 -- negative offsets below an hour
    e["e07_offset_negative_minutes"] = [
        "offset -00:30",
        "offset -00:45",
        "offset -0015",
        "offset -00:59",
        "offset -01:00",
        "offset -00:00",
        'event add a "Odd zone" 2024-03-04T10:00 tz=-00:30',
        "event show a",
        "export text",
        "agenda 2024-03-04 2024-03-04",
    ]
    e["e08_offset_negative_event_edit"] = [
        'event add a "Base" 2024-03-04T10:00 tz=-00:20',
        'event add b "Other" 2024-03-04T10:00 tz=-05:30',
        "event set b tz=-00:05",
        "event show b",
        "list",
        "export pack",
        "check",
    ]
    # M05 -- weekly rules with a step above one when the start falls late in the week
    e["e09_weekly_every2_midweek_start"] = [
        'event add a "Biweekly" 2024-03-06T10:00 rule=weekly;every=2;on=MO,WE,FR',
        "expand a 2024-03-01 2024-05-31",
        'event add b "Triweekly" 2024-03-08T10:00 rule=weekly;every=3;on=MO,TU,FR',
        "expand b 2024-03-01 2024-06-30",
    ]
    e["e10_weekly_every_late_week_start"] = [
        'event add a "Weekend start" 2024-03-09T09:00 rule=weekly;every=2;on=SA,SU,MO,TU;count=10',
        "expand a 2024-03-01 2024-06-30",
        'event add b "Thursday start" 2024-03-07T09:00 rule=weekly;every=4;on=TU,TH',
        "expand b 2024-03-01 2024-09-30",
        "event rule b weekly;every=2;on=MO,TH",
        "expand b 2024-03-01 2024-05-15",
    ]
    # M06 -- a start that rounds up past midnight
    e["e11_snap_carry_into_next_day"] = [
        "snap 2024-03-04T23:59:30",
        "snap 2024-03-04T23:59:59",
        "snap 2024-03-31T23:59:45",
        "snap 2024-12-31T23:59:30",
        "snap 2024-02-28T23:59:31",
        "snap 2024-02-29T23:59:30",
        "snap 2023-02-28T23:59:30",
        "snap 2024-03-04T23:59:29",
        "snap 2024-03-04T23:58:30",
    ]
    e["e12_snap_carry_events"] = [
        'event add a "Late start" 2024-03-04T23:59:45 dur=1h rule=daily;count=3',
        "event show a",
        "expand a 2024-03-01 2024-03-10",
        'event add b "Year end" 2024-12-31T23:59:30',
        "event show b",
        "event move a 2024-03-09T23:59:50",
        "event show a",
        "agenda 2024-03-01 2024-03-31",
        "export text",
    ]
    # M07 -- ids that tie on their first two chunks, same start and priority
    e["e13_agenda_ties_multi_number_ids"] = [
        'event add r2d10 "Ten" 2024-05-06T09:00',
        'event add r2d9 "Nine" 2024-05-06T09:00',
        'event add r2d100 "Hundred" 2024-05-06T09:00',
        'event add r2d9b "Nine b" 2024-05-06T09:00',
        "agenda 2024-05-06 2024-05-06",
        "busy 2024-05-06 2024-05-06",
    ]
    e["e14_agenda_ties_text_after_number"] = [
        'event add room1-z "Z" 2024-05-06T09:00 prio=3',
        'event add room1-a "A" 2024-05-06T09:00 prio=3',
        'event add room1 "Plain" 2024-05-06T09:00 prio=3',
        'event add room01 "Zero" 2024-05-06T09:00 prio=3',
        'event add room1-a2 "A two" 2024-05-06T09:00 prio=3',
        'event add room1-a10 "A ten" 2024-05-06T09:00 prio=3',
        "agenda 2024-05-06 2024-05-06",
        "list",
    ]
    # M08 -- the largest sequence numbers
    e["e15_reference_maximum"] = [
        "ref 1125899906842623",
        "ref 1125899906842622",
        "ref 1125899906842621",
        "ref 1125899906842620",
        "unref ZZZZZZZZZZ",
        "idseq 1125899906842623",
        'event add - "Last" 2024-05-05T10:00',
        "event show #ZZZZZZZZZZ",
        "list",
        'event add - "None left" 2024-05-05T11:00',
    ]
    e["e16_reference_before_maximum"] = [
        "idseq 1125899906842620",
        'event add - "Four from the end" 2024-05-05T10:00',
        'event add - "Three" 2024-05-05T11:00',
        'event add - "Two" 2024-05-05T12:00',
        "list",
        "check",
    ]
    # M09 -- skips after a move that changes which dates the series selects
    e["e17_move_drops_stale_skips"] = [
        'event add a "Weekly" 2024-03-04T10:00 rule=weekly',
        "skip a 2024-03-11",
        "skip a 2024-03-25",
        "event move a 2024-03-07T10:00",
        "event show a",
        "expand a 2024-03-01 2024-04-30",
        "skip a 2024-03-25",
    ]
    e["e18_move_drops_stale_skips_monthly"] = [
        'event add a "Monthly" 2024-01-10T10:00 rule=monthly',
        "skip a 2024-02-10",
        "skip a 2024-04-10",
        "event move a 2024-01-20T10:00",
        "event show a",
        'event add b "Yearly" 2024-05-05T10:00 rule=yearly;count=5',
        "skip b 2026-05-05",
        "event move b 2024-05-06T10:00",
        "event show b",
        "check",
    ]
    # M10 -- runs of blanks in titles
    e["e19_title_long_blank_runs"] = [
        'title "three   spaces"',
        'title "four    spaces"',
        'title "  lead and trail   "',
        'title "tabs\t\t\tand   spaces"',
        'title "a \t b"',
        'event add a "Planning   session   notes" 2024-03-04T10:00',
        "event show a",
        'event retitle a "Seven       blanks"',
        "event show a",
        "export text",
    ]
    # generated sessions that reach several defects each
    e["e20_session_calendar_values"] = Gen(11, ("civil", "snap", "offset", "title"), 40, 0.25).session(260)
    e["e21_session_codecs"] = Gen(12, ("cats", "varint", "ref"), 40, 0.25).session(260)
    e["e22_session_ordering_state"] = Gen(13, ("weekly", "natural", "move"), 40, 0.35).session(260)
    return e


def main():
    smoke_dir = os.path.join(TASK, "public", "smoke")
    for name, lines in SMOKE.items():
        write(smoke_dir, name, lines)
    for name, lines in ref_tests().items():
        write(os.path.join(HERE, "ref_tests"), name, lines)
    for name, lines in ref_edge().items():
        write(os.path.join(HERE, "ref_edge"), name, lines)
    print("inputs written")


if __name__ == "__main__":
    main()
