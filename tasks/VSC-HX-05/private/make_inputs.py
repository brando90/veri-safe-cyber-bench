#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write the .in files for public/smoke, private/ref_tests and private/ref_edge.

Inputs are the source of truth; the .out files are produced from gold by
build_private.sh.  All data is ordinary business data (names with
apostrophes, quotes, backslashes, tabs; ordinary role setups).
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TASK = ROOT.parent
T = "\t"

BASE = [
    "as owner",
    "user-add fay frontdesk",
    "user-add bill billing",
    "user-add tom trainee",
    "user-add mia manager",
    "service-add CUT 30 25.00 8.25 Haircut",
    "service-add WASH 15 12.25 10 Wash and dry",
    "service-add TRIM 20 18.50 8.25 Beard trim",
    "service-add COLOR 60 49.99 20 Colour treatment",
    "customer-add 555-0100 ann@example.com Ann O'Neil",
    "customer-add 555-0101 - Bob Jones",
    "customer-add 555-0102 cy@example.org Cy Park",
]

BOOK = [
    "as fay",
    "book C1 CUT 2026-03-02 09:00",
    "book C1 WASH 2026-03-02 09:30",
    "book C2 TRIM 2026-03-02 10:00",
    "book C3 COLOR 2026-03-03 14:00",
    "book C2 CUT 2026-03-04 08:00",
    "appt-status A1 done",
    "appt-status A2 done",
    "appt-status A3 done",
    "appt-status A4 noshow",
]


def block(kind, header, rows):
    return ["import " + kind, T.join(header)] + [T.join(r) for r in rows] + [".end"]


# ======================================================================== smoke

SMOKE = {
    "s1_roles_and_customers": BASE + [
        "whoami", "perms frontdesk", "perms billing",
        "as fay", "whoami",
        "customer-add 555-0199 dee@example.com Dee Lee",
        "customer-note C4 Prefers mornings",
        "customer-show C4", "customer-find lee", "customer-find o'n",
        "as nobody", "customer-find lee",
    ],
    "s2_booking": BASE + BOOK + [
        "book C3 TRIM 2026-03-02 09:10",
        "book C3 TRIM 2026-03-02 17:50",
        "appts 2026-03-02", "services",
        "as mia", "cancel A5", "appts 2026-03-04",
    ],
    "s3_billing_reports": BASE + BOOK + [
        "as bill",
        "invoice-create C1",
        "invoice-create C2 20",
        "invoice-show I1", "invoice-show I2",
        "pay I1 20 card", "pay I1 18.38 cash",
        "report revenue 2026-03-01 2026-03-31",
        "report tax 2026-03-01 2026-03-31",
        "report balances", "report balances tsv",
    ],
    "s4_import_export": BASE + [
        "import customers",
        T.join(["name", "phone", "note"]),
        T.join(["Eve Stone", "555-0200", "walk-in"]),
        T.join(["Finn Hale", "555-0201", ""]),
        ".end",
        "export customers csv", "export services tsv", "audit 3",
    ],
    "s5_errors": [
        "# setup", "",
        "customer-add 555-0100 - Nobody's customer",
        "as ghost", "as owner",
        "customer-add 12 - Short phone",
        "customer-add 555-0100 not-an-email Name",
        "service-add cut 30 25.00 8.25 Lower case code",
        "service-add CUT 7 25.00 8.25 Odd minutes",
        "service-add CUT 30 25.001 8.25 Too many decimals",
        "book C1 CUT 2026-02-30 09:00",
        "frobnicate", "report", "pay I1 10 card",
    ],
}

# ======================================================================== ref_tests

REF_TESTS = {
    "t01_builtin_roles": BASE + [
        "perms viewer", "perms frontdesk", "perms trainee", "perms billing",
        "perms manager", "perms owner", "perms nosuch",
        "as tom", "whoami", "as nobody", "whoami", "as bill", "whoami",
    ],
    "t02_custom_roles_plain": BASE + [
        "role-add desk frontdesk", "role-grant desk invoice.view", "role-deny desk appt.write",
        "perms desk",
        "role-add mixed frontdesk,billing", "perms mixed",
        "role-grant mixed audit.view", "perms mixed",
        "role-add desk x", "role-add desk2 frontdesk,,billing", "role-add desk3 frontdesk,frontdesk",
        "role-add desk frontdesk", "role-grant manager audit.view", "role-grant desk no.such",
        "role-grant desk invoice.view", "role-deny desk invoice.view", "perms desk",
        "user-add ivy desk", "user-add ivy viewer", "user-add Ivy viewer", "user-add zed ghost",
        "as ivy", "whoami", "book C1 CUT 2026-03-02 09:00", "customer-add 555-0300 - Ivy's friend",
        "as fay", "role-add nope viewer",
    ],
    "t03_frontdesk_status_changes": BASE + BOOK + [
        "book C3 CUT 2026-03-05 11:00",
        "appt-status A5 noshow", "appt-status A6 done", "appt-status A6 noshow",
        "appt-status A6 later",
        "as tom", "book C3 TRIM 2026-03-05 12:00", "appt-status A7 done",
        "customer-add 555-0400 - Trainee customer", "customer-note C1 Nope",
        "appts 2026-03-05",
    ],
    "t04_archive": BASE + BOOK + [
        "book C3 CUT 2026-03-06 09:00", "book C3 TRIM 2026-03-07 09:00",
        "customer-archive C1", "customer-add 555-0410 - Walk In", "customer-archive C4",
        "customer-archive C2",
        "customer-archive C3",
        "as mia", "customer-archive C3", "customer-archive C3", "customer-show C3",
        "customer-find park", "book C3 CUT 2026-03-08 09:00", "customer-note C3 gone",
        "as owner", "audit 4",
    ],
    "t05_billing_rounding": BASE + BOOK + [
        "as fay", "book C3 WASH 2026-03-05 09:00", "book C3 WASH 2026-03-05 09:15",
        "book C3 COLOR 2026-03-05 10:00",
        "appt-status A6 done", "appt-status A7 done", "appt-status A8 done",
        "as bill",
        "invoice-create C3 10", "invoice-show I1",
        "invoice-create C1 15", "invoice-show I2",
        "invoice-create C1", "invoice-create C2 101", "invoice-create C2 5",
        "invoice-show I3",
        "pay I1 0 cash", "pay I1 0.5 card", "pay I1 100 card", "pay I1 3.99 cheque",
        "invoice-show I1", "invoice-void I1 Typo", "as mia", "invoice-void I1 Typo",
        "invoice-void I2 Wrong discount", "invoice-void I2 again", "invoice-create C1",
        "invoice-show I4", "pay I2 1 cash",
        "report balances",
    ],
    "t06_reports_plain": BASE + BOOK + [
        "as bill", "invoice-create C1", "invoice-create C2",
        "report revenue 2026-03-01 2026-03-31",
        "report revenue 2026-03-02 2026-03-02 tsv",
        "report revenue 2026-03-03 2026-03-03",
        "report tax 2026-03-01 2026-03-31",
        "report tax 2026-03-01 2026-03-31 tsv",
        "report tax 2026-04-01 2026-03-01",
        "report revenue 2026-03-01", "report weekly 2026-03-01 2026-03-02",
        "report balances", "report balances tsv",
        "as mia", "invoice-void I2 Customer disputes", "report balances",
        "report revenue 2026-03-01 2026-03-31",
    ],
    "t07_special_text_plain": BASE + [
        'customer-add 555-0500 - Dana "DJ" Smith, Jr.',
        "customer-add 555-0501 - Lee\\Park Studio",
        "customer-add 555-0502 - 50% Off | Bargain_Cuts; Ltd",
        "customer-note C4 Call before 9; ask for \"Dana\"",
        "customer-note C5 Folder: C:\\clients\\lee" + T + "(scanned)",
        "customer-note C6    spaced   out   ",
        "customer-show C4", "customer-show C5", "customer-show C6",
        "customer-find 50%", "customer-find _", "customer-find \"dj\"", "customer-find \\",
        "customer-find o'neil", "customer-find %",
        "export customers csv", "export customers tsv",
        "audit",
    ],
    "t08_import_valid": BASE + BOOK + [
        "as bill", "invoice-create C1", "invoice-create C2",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I1", "10.00", "card"]),
        T.join(["I2", "5", "cash"]),
        ".end",
        "invoice-show I1",
        "as owner",
        "import customers",
        T.join(["phone", "name"]),
        T.join(["555-0600", "Gus Grey"]),
        "",
        T.join(["555-0601", "Hana Holt"]),
        ".end",
        "import services",
        T.join(["code", "name", "minutes", "price", "tax"]),
        T.join(["NAILS", "Nail care", "25", "15", "8.25"]),
        ".end",
        "import appointments",
        T.join(["customer", "service", "day", "time"]),
        T.join(["C4", "NAILS", "2026-03-09", "09:00"]),
        T.join(["C5", "CUT", "2026-03-09", "09:25"]),
        ".end",
        "appts 2026-03-09",
        "import customers",
        T.join(["name", "phone", "phone"]),
        ".end",
        "import customers",
        T.join(["name"]),
        ".end",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Ok Row", "555-0700"]),
        T.join(["Bad Row", "x"]),
        ".end",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Short"]),
        ".end",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Odd \\q escape", "555-0701"]),
        ".end",
        "import customers",
        "",
        ".end",
        "import vendors",
        "name",
        ".end",
        "import appointments",
        T.join(["customer", "service", "day", "time"]),
        T.join(["C4", "CUT", "2026-03-09", "09:10"]),
        ".end",
        "customer-find h",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Never Ends", "555-0800"]),
    ],
    "t09_big_import": None,  # generated below
    "t10_whitespace_comments": [
        "   # leading comment",
        "\tas\towner\t",
        "service-add   CUT   30   25.00   8.25    Haircut   ",
        "customer-add 555-0100\t-\t  Ann   O'Neil  ",
        "customer-show C0001",
        "customer-show C1   extra",
        "",
        "   ",
        "book C1 CUT 2026-03-02 09:00\r",
        "appts 2026-03-02\r",
        "import customers",
        T.join(["name", "phone"]),
        "",
        T.join(["Blank Lines", "555-0101"]),
        "",
        "   .end   ",
        "customer-find blank",
        ".end",
        "WHOAMI",
        "whoami now",
    ],
    "t11_error_messages": BASE + [
        "user-add owner viewer", "user-add nobody viewer", "user-add x1",
        "role-grant viewer appt.write", "role-deny ghost appt.write",
        "customer-add 555-0100 - " + "N" * 81,
        "customer-add 555-0100 a@b@c Name", "customer-add 555-0100 -",
        "customer-note C9 hello", "customer-note X1 hello", "customer-note C0 hello",
        "customer-note C1 " + "n" * 201,
        "service-add CUT 30 25.00 8.25 Duplicate", "service-add LONGCODE9 30 1 1 Long",
        "service-add NEW 30 1 100.01 Over rate", "service-add NEW 485 1 1 Long service",
        "book C1 NOPE 2026-03-02 09:00", "book C1 CUT 2026-03-02 09:03",
        "book C1 CUT 2026-03-02 07:55", "book C1 COLOR 2026-03-02 17:30",
        "book C1 CUT 2026-03-02 24:00", "book C1 CUT 2026-3-2 09:00",
        "appt-status A1 done", "cancel A1", "appts", "appts 2026-13-01",
        "invoice-create C1", "invoice-show I1", "pay I1 10 card", "invoice-void I1 x",
        "audit 0", "audit x", "audit 2 3", "audit 2",
        "export customers xml", "export people csv", "export customers",
        "import", "import customers extra", ".end",
    ],
    "t12_permission_order": BASE + BOOK + [
        "as bill", "audit-export", "audit", "export customers csv",
        "as fay", "audit-export", "export customers csv",
        "appt-status A9 cancelled", "appt-status A5 sleeping",
        "customer-archive C9", "cancel A5",
        "as nobody", "import customers", T.join(["name", "phone"]),
        T.join(["Never", "555-0900"]), ".end", "customer-find never",
        "as tom", "customer-archive C1", "import customers", T.join(["name", "phone"]), ".end",
        "as owner", "customer-find never",
    ],
    "t13_export_all": BASE + BOOK + [
        "as bill", "invoice-create C1", "invoice-create C2", "pay I2 20.03 transfer",
        "as mia", "invoice-void I1 Re-issue", "as bill", "invoice-create C1 50",
        "export services csv", "export services tsv",
        "export appointments csv", "export appointments tsv",
        "export invoices csv", "export invoices tsv",
        "as fay", "export customers csv",
    ],
    "t14_cancel_flows": BASE + BOOK + [
        "as mia", "cancel A5", "cancel A5", "appt-status A1 cancelled",
        "book C1 CUT 2026-03-04 08:00", "appt-status A6 cancelled",
        "book C1 CUT 2026-03-04 08:10", "appts 2026-03-04",
        "as owner", "audit 5",
    ],
    "t15_import_audit_plain": BASE + [
        "import customers",
        T.join(["name", "phone", "email", "note"]),
        T.join(["Ian Moss", "555-1000", "ian@example.com", "regular"]),
        T.join(["Jo Kemp", "555-1001", "-", "allergic to lavender"]),
        ".end",
        "import services",
        T.join(["tax", "price", "minutes", "name", "code"]),
        T.join(["10", "9.90", "10", "Quick tidy", "TIDY"]),
        ".end",
        "audit 3", "audit-export",
    ],
    "t16_payments_import_errors": BASE + BOOK + [
        "as bill", "invoice-create C1",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I1", "20", "card"]),
        T.join(["I1", "30", "card"]),
        ".end",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I1", "20", "card"]),
        T.join(["I1", "18.38", "cash"]),
        ".end",
        "invoice-show I1", "pay I1 1 cash",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I9", "1", "card"]),
        ".end",
    ],
}


def big_import():
    lines = list(BASE)
    lines += ["import customers", T.join(["name", "phone", "email", "note"])]
    for i in range(3000):
        lines.append(T.join(["Client %04d O'Hara" % i, "555-%04d" % (i % 10000),
                             "c%d@example.com" % i if i % 3 else "-", "batch %d" % (i % 7)]))
    lines.append(".end")
    lines += ["as fay"]
    day = 1
    hour = 8
    for i in range(300):
        cust = "C%d" % (4 + i * 7)
        lines.append("book %s CUT 2026-04-%02d %02d:00" % (cust, day, hour))
        lines.append("appt-status A%d done" % (i + 1))
        hour += 1
        if hour == 18:
            hour = 8
            day += 1
    lines += ["as bill"]
    for i in range(0, 300, 3):
        lines.append("invoice-create C%d %d" % (4 + i * 7, i % 20))
    lines += ["report revenue 2026-04-01 2026-04-30", "report balances tsv",
              "as owner", "customer-find client 2999", "customer-find O'HARA",
              "audit 3", "customer-show C3003"]
    return lines


REF_TESTS["t09_big_import"] = big_import()

# ======================================================================== ref_edge

REF_EDGE = {
    # --- import header (D1)
    "e01_import_services_extra_column": BASE + [
        "import services",
        T.join(["code", "name", "minutes", "price", "tax", "colour"]),
        T.join(["NAILS", "Nail care", "25", "15", "8.25", "red"]),
        ".end",
        "services",
    ],
    "e02_import_customers_extra_column": BASE + [
        "import customers",
        T.join(["name", "phone", "vip"]),
        T.join(["Kim Ray", "555-1100", "yes"]),
        ".end",
        "customer-find kim",
    ],
    "e03_import_appointments_status_column": BASE + [
        "import appointments",
        T.join(["customer", "service", "day", "time", "status"]),
        T.join(["C1", "CUT", "2026-03-10", "09:00", "done"]),
        ".end",
        "appts 2026-03-10",
        "as bill", "invoice-create C1",
    ],
    # --- audit export escaping (D2)
    "e04_audit_export_quoted_name": BASE + [
        'customer-add 555-0500 - Dana "DJ" Smith',
        "as mia", "audit-export",
    ],
    "e05_audit_export_note_and_reason": BASE + BOOK + [
        "as fay", "customer-note C2 See folder C:\\cards" + T + "and ask",
        "as bill", "invoice-create C1",
        "as mia", 'invoice-void I1 Customer said "wrong date"',
        "audit-export",
    ],
    # --- bulk audit rows of imports (D3)
    "e06_import_customer_quoted": BASE + [
        "import customers",
        T.join(["name", "phone", "note"]),
        T.join(['Pat "Patch" Doyle', "555-1200", "plain"]),
        T.join(["Quinn Roe", "555-1201", 'likes "quiet" chair']),
        ".end",
        "audit 2", "customer-show C4",
    ],
    "e07_import_backslash_tab": BASE + [
        "import customers",
        T.join(["name", "phone", "note"]),
        T.join(["Rae Lin", "555-1300", "folder D:\\\\scans\\tback room"]),
        ".end",
        "import services",
        T.join(["code", "name", "minutes", "price", "tax"]),
        T.join(["DELUXE", 'The "works"', "45", "39", "8.25"]),
        ".end",
        "audit 2", "customer-show C4", "services",
    ],
    # --- cancelling through appt-status (D4)
    "e08_frontdesk_status_cancelled": BASE + BOOK + [
        "book C3 CUT 2026-03-05 09:00",
        "appt-status A6 cancelled", "appts 2026-03-05",
        "as mia", "appt-status A6 cancelled", "appts 2026-03-05",
    ],
    "e09_custom_role_status_cancelled": BASE + [
        "role-add scheduler viewer", "role-grant scheduler appt.write",
        "user-add sam scheduler",
        "as sam", "book C1 CUT 2026-03-05 09:00", "book C2 CUT 2026-03-05 10:00",
        "appt-status A1 done", "appt-status A2 cancelled", "cancel A2", "appts 2026-03-05",
    ],
    # --- import permission per kind (D5)
    "e10_billing_imports_customers": BASE + [
        "as bill",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Uma Vale", "555-1400"]),
        ".end",
        "customer-find uma",
    ],
    "e11_billing_imports_other_kinds": BASE + BOOK + [
        "as bill", "invoice-create C1",
        "import appointments",
        T.join(["customer", "service", "day", "time"]),
        T.join(["C2", "CUT", "2026-03-11", "09:00"]),
        ".end",
        "import services",
        T.join(["code", "name", "minutes", "price", "tax"]),
        T.join(["NAILS", "Nail care", "25", "15", "8.25"]),
        ".end",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I1", "5", "card"]),
        ".end",
        "appts 2026-03-11", "services", "invoice-show I1",
    ],
    "e12_custom_importer_role": BASE + BOOK + [
        "as owner", "role-add importer frontdesk", "role-grant importer import.run",
        "user-add ola importer",
        "as bill", "invoice-create C1",
        "as ola",
        "import customers",
        T.join(["name", "phone"]),
        T.join(["Vic West", "555-1500"]),
        ".end",
        "import services",
        T.join(["code", "name", "minutes", "price", "tax"]),
        T.join(["NAILS", "Nail care", "25", "15", "8.25"]),
        ".end",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        T.join(["I1", "5", "card"]),
        ".end",
        "customer-find vic", "services", "invoice-show I1",
    ],
    # --- deny anywhere in the chain (D6)
    "e13_deny_from_parent_beats_other_parent": BASE + [
        "role-add mgrtrainee trainee,manager", "perms mgrtrainee",
        "user-add max mgrtrainee",
        "as max", "customer-add 555-1600 - Max's client", "book C1 CUT 2026-03-05 09:00",
        "cancel A1",
    ],
    "e14_child_grant_cannot_undo_ancestor_deny": BASE + [
        "role-add desk2 trainee", "role-grant desk2 customer.write", "perms desk2",
        "user-add dot desk2",
        "as dot", "customer-add 555-1700 - Dot's client", "customer-note C1 hello",
    ],
    "e15_deny_two_levels_up": BASE + [
        "role-add base frontdesk", "role-deny base appt.write",
        "role-add mid base", "role-add top mid,manager", "perms top",
        "user-add tia top",
        "as tia", "book C1 CUT 2026-03-05 09:00", "customer-add 555-1800 - Tia's client",
    ],
    # --- change to a role reaches its descendants (D7)
    "e16_deny_reaches_grandchild": BASE + [
        "role-add senior frontdesk", "role-add junior senior", "role-add intern junior",
        "user-add jo intern",
        "as jo", "customer-add 555-1900 - First client",
        "as owner", "perms intern", "role-deny senior customer.write", "perms junior",
        "perms intern",
        "as jo", "customer-add 555-1901 - Second client", "customer-find client",
    ],
    "e17_grant_reaches_child": BASE + [
        "role-add helper viewer", "role-add helper2 helper", "perms helper2",
        "user-add hal helper2",
        "as hal", "book C1 CUT 2026-03-05 09:00",
        "as owner", "role-grant helper appt.write", "perms helper", "perms helper2",
        "as hal", "book C1 CUT 2026-03-05 09:00",
    ],
    # --- tax report rounding (D8)
    "e18_tax_report_per_line": BASE + [
        "as fay",
        "book C1 CUT 2026-03-02 09:00", "book C2 CUT 2026-03-02 10:00",
        "appt-status A1 done", "appt-status A2 done",
        "as bill", "invoice-create C1", "invoice-create C2",
        "report tax 2026-03-01 2026-03-31", "report revenue 2026-03-01 2026-03-31",
    ],
    "e19_tax_report_tsv_discounts": BASE + [
        "as fay",
        "book C1 CUT 2026-03-02 09:00", "book C1 TRIM 2026-03-02 09:30",
        "book C2 CUT 2026-03-02 10:00", "book C3 WASH 2026-03-02 11:00",
        "book C3 WASH 2026-03-02 11:15", "book C3 WASH 2026-03-02 11:30",
        "appt-status A1 done", "appt-status A2 done", "appt-status A3 done",
        "appt-status A4 done", "appt-status A5 done", "appt-status A6 done",
        "as bill", "invoice-create C1 10", "invoice-create C2 10", "invoice-create C3 3",
        "report tax 2026-03-01 2026-03-31 tsv", "report tax 2026-03-02 2026-03-02",
    ],
    # --- mixed
    "e20_mixed_day": BASE + BOOK + [
        "as owner", "role-add lead trainee,billing", "role-grant lead appt.cancel",
        "user-add lu lead",
        "as lu", "customer-add 555-2000 - Lu's client",
        "book C3 CUT 2026-03-05 09:00", "appt-status A6 cancelled",
        "import payments",
        T.join(["invoice", "amount", "method"]),
        ".end",
        "import customers",
        T.join(["name", "phone", "note"]),
        T.join(['Wes "Doc" Hart', "555-2001", ""]),
        ".end",
        "as owner",
        "import customers",
        T.join(["name", "phone", "note"]),
        T.join(['Wes "Doc" Hart', "555-2001", "back\\\\door"]),
        ".end",
        "audit 3", "audit-export",
    ],
}


def write(dirpath, cases):
    dirpath.mkdir(parents=True, exist_ok=True)
    for old in dirpath.glob("*.in"):
        old.unlink()
    for old in dirpath.glob("*.out"):
        old.unlink()
    for name, lines in cases.items():
        (dirpath / (name + ".in")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    write(TASK / "public" / "smoke", SMOKE)
    write(ROOT / "ref_tests", REF_TESTS)
    write(ROOT / "ref_edge", REF_EDGE)
    print("inputs written: %d smoke, %d ref_tests, %d ref_edge"
          % (len(SMOKE), len(REF_TESTS), len(REF_EDGE)))


if __name__ == "__main__":
    main()
