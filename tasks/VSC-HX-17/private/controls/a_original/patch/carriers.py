# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The carrier registry: every module by code."""

from errors import CommandError

import car_swift
import car_parcelo
import car_haul
import car_aero
import car_nord
import car_gull
import car_tern
import car_pony
import car_zed

MODULES = {
    "swift": car_swift,
    "parcelo": car_parcelo,
    "haul": car_haul,
    "aero": car_aero,
    "nord": car_nord,
    "gull": car_gull,
    "tern": car_tern,
    "pony": car_pony,
    "zed": car_zed,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def checked(code):
    if code not in MODULES:
        raise CommandError("unknown_carrier", code)
    return MODULES[code]


def codes():
    return sorted(MODULES)


def all_modules():
    return [MODULES[c] for c in sorted(MODULES)]


def eligible(car, region, weight, haz):
    return car.covers(region.CODE) and car.eligible(weight, haz)


def choose(pref, region, wh, weight, haz, distance):
    """The carrier module for a shipment: the named one if PREF is a carrier
    code, else the cheapest eligible one (ties: faster, then by code)."""
    if pref != "auto":
        car = checked(pref)
        if not eligible(car, region, weight, haz):
            raise CommandError("carrier_ineligible", pref, wh.CODE, region.CODE)
        return car
    best = None
    for car in all_modules():
        if not eligible(car, region, weight, haz):
            continue
        key = (car.cost(weight, distance), car.transit(distance), car.CODE)
        if best is None or key < best[0]:
            best = (key, car)
    if best is None:
        raise CommandError("no_carrier", wh.CODE, region.CODE)
    return best[1]
