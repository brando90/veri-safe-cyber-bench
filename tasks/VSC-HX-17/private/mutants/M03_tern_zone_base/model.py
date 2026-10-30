# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Plain records of the simulation."""
from dataclasses import dataclass, field


@dataclass
class Customer:
    id: str
    name: str
    region: str
    tier: str = "basic"
    carrier: str = "auto"
    split: bool = True
    hold: bool = False
    po: str = ""
    email: str = ""
    note: str = ""
    status: str = "active"
    created: int = 0


@dataclass
class Lot:
    id: str
    wh: str
    sku: str
    qty: int
    reserved: int
    expiry: object
    received: int


@dataclass
class Line:
    sku: str
    qty: int
    allocs: list = field(default_factory=list)
    backorder: int = 0
    shipped: int = 0
    returned: int = 0
    cancelled: int = 0
    ship_day: int = -1
    ship_wh: str = ""

    def allocated(self):
        return sum(a[2] for a in self.allocs)

    def pending(self):
        return self.allocated() + self.backorder


@dataclass
class Order:
    number: str
    cust: str
    day: int
    lines: list
    goods: int = 0
    ref: str = ""
    status: str = "open"
    cancelled: bool = False


@dataclass
class Shipment:
    id: str
    order: str
    wh: str
    carrier: str
    lines: list
    weight: int
    goods: int
    freight: int
    handling: int
    duty: int
    day: int
    ship_day: int
    eta: int
    region: str


@dataclass
class Move:
    seq: int
    day: int
    kind: str
    wh: str
    sku: str
    delta: int
    qty: int
    ref: str
