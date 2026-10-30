# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The sku table: category, unit cost and unit price (US cents) of every item."""

import money

# code: (category, cost, price, name)
SKUS = {
    'bolt-m6': ('fasteners', 8, 15, 'Bolt M6'),
    'screw-w4': ('fasteners', 5, 9, 'Wood screw 4mm'),
    'cable-usb': ('cables', 120, 290, 'USB cable per metre'),
    'cable-hdmi': ('cables', 210, 480, 'HDMI cable per metre'),
    'paper-a4': ('paper', 350, 620, 'Paper A4 ream'),
    'paper-a3': ('paper', 610, 990, 'Paper A3 ream'),
    'hammer-1': ('tools', 700, 1450, 'Claw hammer'),
    'wrench-set': ('tools', 1900, 3900, 'Wrench set'),
    'plier-9': ('tools', 800, 1700, 'Pliers 9in'),
    'charger-20': ('electronics', 900, 2200, 'Charger 20W'),
    'speaker-bt': ('electronics', 2400, 5900, 'Bluetooth speaker'),
    'tumbler-6': ('glassware', 150, 390, 'Glass tumbler'),
    'vase-30': ('glassware', 1100, 2600, 'Vase 30cm'),
    'shirt-m': ('apparel', 500, 1400, 'Shirt medium'),
    'jacket-l': ('apparel', 2300, 5500, 'Jacket large'),
    'crisps-50': ('snacks', 30, 80, 'Crisps 50g'),
    'bar-oat': ('snacks', 25, 70, 'Oat bar'),
    'milk-1l': ('dairy', 60, 120, 'Milk 1l'),
    'yogurt-4': ('dairy', 140, 290, 'Yogurt 4-pack'),
    'apple-1k': ('produce', 120, 260, 'Apples 1kg'),
    'lettuce-1': ('produce', 50, 130, 'Lettuce head'),
    'vitamin-c': ('medicine', 200, 520, 'Vitamin C tablets'),
    'bandage-50': ('medicine', 180, 450, 'Bandages 50'),
    'pizza-fr': ('frozen', 180, 420, 'Frozen pizza'),
    'peas-fr': ('frozen', 90, 200, 'Frozen peas'),
    'thinner-1l': ('solvents', 400, 900, 'Thinner 1l'),
    'cleaner-5l': ('solvents', 900, 1900, 'Cleaner 5l'),
    'plank-2m': ('lumber', 350, 780, 'Plank 2m'),
    'beam-3m': ('lumber', 900, 2000, 'Beam 3m'),
}


def known(code):
    return code in SKUS


def codes():
    return sorted(SKUS)


def category(code):
    return SKUS[code][0]


def cost(code):
    return SKUS[code][1]


def price(code):
    return SKUS[code][2]


def name(code):
    return SKUS[code][3]


def describe(code):
    return "%s category=%s cost=%s price=%s" % (code, category(code),
                                                money.fmt(cost(code)), money.fmt(price(code)))
