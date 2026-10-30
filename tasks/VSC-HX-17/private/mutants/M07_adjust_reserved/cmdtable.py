# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""The command table: command words, handler and usage line."""

import adjust
import audit
import backorders
import catalog
import clockcmd
import customers
import expiry
import export
import helptext
import orders
import receiving
import replenish
import reportcmd
import returns
import set_carrier
import set_email
import set_hold
import set_name
import set_note
import set_po
import set_region
import set_split
import set_tier
import shipping
import stockcmd
import tiers
import transfers
from errors import CommandError

COMMANDS = {
    ('today',): (clockcmd.cmd_today, 'today'),
    ('tick',): (clockcmd.cmd_tick, 'tick DAYS'),
    ('customer', 'add'): (customers.cmd_add, 'customer add ID REGION [tier=TIER] [name=TEXT]'),
    ('customer', 'show'): (customers.cmd_show, 'customer show ID'),
    ('customer', 'list'): (customers.cmd_list, 'customer list [tier=TIER] [region=REGION] [status=active|closed]'),
    ('customer', 'close'): (customers.cmd_close, 'customer close ID'),
    ('customer', 'history'): (customers.cmd_history, 'customer history ID'),
    ('sku', 'list'): (catalog.cmd_sku_list, 'sku list'),
    ('sku', 'show'): (catalog.cmd_sku_show, 'sku show SKU'),
    ('warehouse', 'list'): (catalog.cmd_warehouse_list, 'warehouse list'),
    ('warehouse', 'show'): (catalog.cmd_warehouse_show, 'warehouse show WAREHOUSE'),
    ('category', 'list'): (catalog.cmd_category_list, 'category list'),
    ('category', 'show'): (catalog.cmd_category_show, 'category show CATEGORY'),
    ('carrier', 'list'): (catalog.cmd_carrier_list, 'carrier list'),
    ('carrier', 'show'): (catalog.cmd_carrier_show, 'carrier show CARRIER'),
    ('region', 'list'): (catalog.cmd_region_list, 'region list'),
    ('region', 'show'): (catalog.cmd_region_show, 'region show REGION'),
    ('tier', 'list'): (tiers.cmd_list, 'tier list'),
    ('receive',): (receiving.cmd_receive, 'receive WAREHOUSE SKU UNITS [exp=DAY]'),
    ('stock',): (stockcmd.cmd_stock, 'stock [WAREHOUSE] [sku=SKU]'),
    ('adjust',): (adjust.cmd_adjust, 'adjust WAREHOUSE SKU DELTA'),
    ('transfer',): (transfers.cmd_transfer, 'transfer FROM TO SKU UNITS'),
    ('expire',): (expiry.cmd_expire, 'expire [WAREHOUSE]'),
    ('replenish',): (replenish.cmd_replenish, 'replenish [WAREHOUSE]'),
    ('order', 'add'): (orders.cmd_add, 'order add CUSTOMER SKU:QTY... [ref=TEXT]'),
    ('order', 'show'): (orders.cmd_show, 'order show NUMBER'),
    ('order', 'list'): (orders.cmd_list, 'order list [CUSTOMER] [state=STATE]'),
    ('order', 'cancel'): (orders.cmd_cancel, 'order cancel NUMBER'),
    ('backorder', 'run'): (backorders.cmd_run, 'backorder run'),
    ('ship',): (shipping.cmd_ship, 'ship NUMBER [at=HOUR] [carrier=CARRIER]'),
    ('return',): (returns.cmd_return, 'return NUMBER SKU QTY [cond=good|damaged]'),
    ('ledger',): (stockcmd.cmd_ledger, 'ledger [WAREHOUSE] [kind=KIND] [sku=SKU]'),
    ('audit',): (audit.cmd_audit, 'audit [COUNT] [action=TEXT] [subject=TEXT]'),
    ('export',): (export.cmd_export, 'export KIND FORMAT'),
    ('report',): (reportcmd.cmd_report, 'report NAME [ARGS]'),
    ('set', 'region'): (set_region.cmd_set_region, 'set region ID REGION'),
    ('set', 'tier'): (set_tier.cmd_set_tier, 'set tier ID TIER'),
    ('set', 'carrier'): (set_carrier.cmd_set_carrier, 'set carrier ID CARRIER|auto'),
    ('set', 'split'): (set_split.cmd_set_split, 'set split ID yes|no'),
    ('set', 'hold'): (set_hold.cmd_set_hold, 'set hold ID yes|no'),
    ('set', 'po'): (set_po.cmd_set_po, 'set po ID TEXT'),
    ('set', 'name'): (set_name.cmd_set_name, 'set name ID TEXT'),
    ('set', 'email'): (set_email.cmd_set_email, 'set email ID ADDRESS'),
    ('set', 'note'): (set_note.cmd_set_note, 'set note ID TEXT'),
    ('help',): (helptext.cmd_help, 'help [COMMAND]'),
}


def resolve(cmd):
    words = cmd.words
    for n in (2, 1):
        entry = COMMANDS.get(tuple(words[:n]))
        if entry is not None:
            cmd.name = " ".join(words[:n])
            cmd.args = words[n:]
            cmd.usage = entry[1]
            return entry[0]
    raise CommandError("unknown_command", words[0])


def listing():
    return [(words, COMMANDS[words][1]) for words in sorted(COMMANDS)]
