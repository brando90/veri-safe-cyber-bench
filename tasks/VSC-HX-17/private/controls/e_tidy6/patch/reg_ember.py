# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Region ember: Ember Plains."""
import money
import timeutil

CODE = "ember"
NAME = "Ember Plains"
ZONE = 5
WEEKEND = (5, 6)
BAN_HAZ = 3
DUTY_FREE = 8000
DUTY_BP = 1200
CUSTOMS_DAYS = 2
REMOTE_FEE = 300


def allows(haz):
    """True if goods of hazard class HAZ may be delivered here."""
    return haz < BAN_HAZ


def dutiable(value):
    """True if goods worth VALUE cents carry import duty."""
    return DUTY_BP > 0 and value > DUTY_FREE


def duty(value):
    """Duty in cents on goods worth VALUE cents."""
    if not dutiable(value):
        return 0
    return money.pct(value, DUTY_BP)


def delivery_day(day, dutiable_goods):
    """First delivery day for a parcel that arrives on DAY."""
    if dutiable_goods:
        day += CUSTOMS_DAYS
    return timeutil.next_free(day, WEEKEND)


def is_pickup():
    return ZONE == 0


def weekend_text():
    return timeutil.days_text(WEEKEND)


def describe():
    return "%s zone=%d weekend=%s ban_haz=%d duty_free=%s duty_bp=%d customs_days=%d remote_fee=%s" % (
        CODE, ZONE, weekend_text(), BAN_HAZ, money.fmt(DUTY_FREE), DUTY_BP, CUSTOMS_DAYS,
        money.fmt(REMOTE_FEE))


def detail():
    return [
        "region %s %s" % (CODE, NAME),
        "  zone %d" % ZONE,
        "  no delivery on %s" % weekend_text(),
        "  refuses hazard class %d and above" % BAN_HAZ,
        "  duty %d bp on goods above %s, %d extra days" % (DUTY_BP, money.fmt(DUTY_FREE), CUSTOMS_DAYS),
        "  remote fee %s per shipment" % money.fmt(REMOTE_FEE),
    ]


def summary():
    return {
        "code": CODE,
        "zone": ZONE,
        "ban": BAN_HAZ,
        "duty_bp": DUTY_BP,
    }
