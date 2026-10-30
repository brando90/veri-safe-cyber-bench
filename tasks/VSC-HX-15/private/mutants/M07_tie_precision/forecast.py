# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Straight-line projection of a shipment's temperature."""
import calib
import units
from errors import CmdError

SAMPLES = 6


def project(rs, minutes):
    """Returns the projected temperature in tenths after the last reading."""
    if len(rs) < 2:
        raise CmdError("need at least two readings")
    recent = rs[-SAMPLES:]
    first, last = recent[0], recent[-1]
    horizon = minutes * units.MIN_MS
    step = units.div_round_half_up((last.temp - first.temp) * horizon, last.ts - first.ts)
    return calib.clamp(last.temp + step)


def verdict(temp, lo, hi):
    if temp < lo:
        return "below"
    if temp > hi:
        return "above"
    return "in"
