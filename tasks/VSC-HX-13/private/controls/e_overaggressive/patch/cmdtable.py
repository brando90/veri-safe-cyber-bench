# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The command table: command words, handler and usage line."""

import audit
import catalog
import clockcmd
import closing
import coupons
import credits
import customers
import dunning
import export
import helptext
import invoice
import invoicing
import ledger
import payments
import planchange
import plans
import refunds
import reportcmd
import set_currency
import set_email
import set_exempt
import set_name
import set_note
import set_phone
import set_po
import set_region
import set_terms
import statements
import usage
import usagebatch
import voids
from errors import CommandError

COMMANDS = {
    ('today',): (clockcmd.cmd_today, 'today'),
    ('tick',): (clockcmd.cmd_tick, 'tick DAYS'),
    ('customer', 'add'): (customers.cmd_add, 'customer add ID PLAN REGION CURRENCY [name=TEXT]'),
    ('customer', 'show'): (customers.cmd_show, 'customer show ID'),
    ('customer', 'list'): (customers.cmd_list, 'customer list [plan=PLAN] [region=REGION] [status=active|closed]'),
    ('customer', 'close'): (closing.cmd_close, 'customer close ID'),
    ('customer', 'history'): (customers.cmd_history, 'customer history ID'),
    ('plan', 'list'): (plans.cmd_list, 'plan list'),
    ('plan', 'show'): (plans.cmd_show, 'plan show PLAN'),
    ('plan', 'set'): (planchange.cmd_set, 'plan set ID PLAN'),
    ('service', 'list'): (catalog.cmd_service_list, 'service list'),
    ('service', 'show'): (catalog.cmd_service_show, 'service show SERVICE'),
    ('region', 'list'): (catalog.cmd_region_list, 'region list'),
    ('currency', 'list'): (catalog.cmd_currency_list, 'currency list'),
    ('region', 'show'): (catalog.cmd_region_show, 'region show REGION'),
    ('quote',): (catalog.cmd_quote, 'quote ID SERVICE UNITS'),
    ('advise',): (catalog.cmd_advise, 'advise ID SERVICE UNITS'),
    ('usage',): (usage.cmd_usage, 'usage ID SERVICE UNITS [day=DAY] [id=TEXT]'),
    ('usage', 'batch'): (usagebatch.cmd_batch, 'usage batch ID SERVICE UNITS... [day=DAY] [id=PREFIX]'),
    ('usage', 'list'): (usage.cmd_list, 'usage list ID [SERVICE]'),
    ('usage', 'summary'): (usage.cmd_summary, 'usage summary ID [PERIOD]'),
    ('coupon', 'add'): (coupons.cmd_add, 'coupon add ID KIND VALUE [until=DAY] [n=COUNT]'),
    ('coupon', 'rm'): (coupons.cmd_rm, 'coupon rm ID NUMBER'),
    ('coupon', 'list'): (coupons.cmd_list, 'coupon list ID'),
    ('coupon', 'kinds'): (coupons.cmd_kinds, 'coupon kinds'),
    ('invoice', 'run'): (invoicing.cmd_run, 'invoice run [PERIOD]'),
    ('invoice', 'show'): (invoice.cmd_show, 'invoice show NUMBER'),
    ('invoice', 'list'): (invoice.cmd_list, 'invoice list [ID] [state=open|paid|void] [period=N]'),
    ('pay',): (payments.cmd_pay, 'pay ID AMOUNT [inv=NUMBER]'),
    ('credit', 'add'): (credits.cmd_add, 'credit add ID AMOUNT'),
    ('refund',): (refunds.cmd_refund, 'refund NUMBER AMOUNT'),
    ('void',): (voids.cmd_void, 'void NUMBER'),
    ('dun',): (dunning.cmd_dun, 'dun'),
    ('statement',): (statements.cmd_statement, 'statement ID [period=N]'),
    ('ledger',): (ledger.cmd_ledger, 'ledger [ID] [kind=KIND]'),
    ('audit',): (audit.cmd_audit, 'audit [COUNT] [action=TEXT] [subject=TEXT]'),
    ('export',): (export.cmd_export, 'export KIND FORMAT'),
    ('report',): (reportcmd.cmd_report, 'report NAME [ARGS]'),
    ('set', 'region'): (set_region.cmd_set_region, 'set region ID REGION'),
    ('set', 'currency'): (set_currency.cmd_set_currency, 'set currency ID CURRENCY'),
    ('set', 'terms'): (set_terms.cmd_set_terms, 'set terms ID DAYS'),
    ('set', 'po'): (set_po.cmd_set_po, 'set po ID TEXT'),
    ('set', 'exempt'): (set_exempt.cmd_set_exempt, 'set exempt ID yes|no'),
    ('set', 'name'): (set_name.cmd_set_name, 'set name ID TEXT'),
    ('set', 'email'): (set_email.cmd_set_email, 'set email ID ADDRESS'),
    ('set', 'phone'): (set_phone.cmd_set_phone, 'set phone ID NUMBER'),
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
