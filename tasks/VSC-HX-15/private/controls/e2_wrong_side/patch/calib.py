# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Logger calibration: clock correction and sensor range."""
from errors import CmdError

SENSOR_MIN = -400
SENSOR_MAX = 600


def clamp(value):
    return max(SENSOR_MIN, min(SENSOR_MAX, value))


def calibrate(raw, offset):
    return clamp(raw + offset)


def correct(ts, offset):
    moved = ts - offset
    if moved < 0:
        raise CmdError("corrected time is before the start of the run")
    return moved
