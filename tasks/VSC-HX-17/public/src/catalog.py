# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Listings of the reference data: skus, warehouses, categories, carriers, regions."""
import carriers
import categories
import regions
import skus
import warehouses
from errors import CommandError


def cmd_sku_list(w, cmd):
    for code in skus.codes():
        w.out.emit(skus.describe(code))


def cmd_sku_show(w, cmd):
    code = cmd.arg(0)
    if not skus.known(code):
        raise CommandError("unknown_sku", code)
    w.out.emit(skus.describe(code))
    for line in categories.get(skus.category(code)).detail():
        w.out.emit("  " + line)


def cmd_warehouse_list(w, cmd):
    for wh in warehouses.all_modules():
        w.out.emit(wh.describe())


def cmd_warehouse_show(w, cmd):
    for line in warehouses.checked(cmd.arg(0)).detail():
        w.out.emit(line)


def cmd_category_list(w, cmd):
    for code in categories.codes():
        w.out.emit(categories.get(code).describe())


def cmd_category_show(w, cmd):
    code = cmd.arg(0)
    if not categories.known(code):
        raise CommandError("unknown_category", code)
    for line in categories.get(code).detail():
        w.out.emit(line)


def cmd_carrier_list(w, cmd):
    for car in carriers.all_modules():
        w.out.emit(car.describe())


def cmd_carrier_show(w, cmd):
    for line in carriers.checked(cmd.arg(0)).detail():
        w.out.emit(line)


def cmd_region_list(w, cmd):
    for reg in regions.all_modules():
        w.out.emit(reg.describe())


def cmd_region_show(w, cmd):
    code = cmd.arg(0)
    if not regions.known(code):
        raise CommandError("unknown_region", code)
    for line in regions.get(code).detail():
        w.out.emit(line)
