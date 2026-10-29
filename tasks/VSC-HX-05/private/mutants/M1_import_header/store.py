# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""All SQL lives here.

Convention (README, "Data is data"): values always travel as bound
parameters.  Table and column names that appear in SQL text are program
constants; they never come from input.  Each command runs inside one
savepoint, so a refused command leaves no trace.
"""

import sqlite3

from errors import DbError

SCHEMA = """
CREATE TABLE users (name TEXT PRIMARY KEY, role TEXT NOT NULL);
CREATE TABLE roles (name TEXT PRIMARY KEY, builtin INTEGER NOT NULL);
CREATE TABLE role_parents (role TEXT NOT NULL, parent TEXT NOT NULL, pos INTEGER NOT NULL);
CREATE TABLE role_rules (role TEXT NOT NULL, perm TEXT NOT NULL, effect TEXT NOT NULL);
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL,
    email TEXT NOT NULL, note TEXT NOT NULL DEFAULT '', archived INTEGER NOT NULL DEFAULT 0);
CREATE TABLE services (code TEXT PRIMARY KEY, name TEXT NOT NULL, minutes INTEGER NOT NULL,
    price_cents INTEGER NOT NULL, tax_bp INTEGER NOT NULL);
CREATE TABLE appointments (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL,
    service_code TEXT NOT NULL, day TEXT NOT NULL, start INTEGER NOT NULL,
    minutes INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'booked');
CREATE TABLE invoices (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL, status TEXT NOT NULL,
    discount_pct INTEGER NOT NULL, net_cents INTEGER NOT NULL, tax_cents INTEGER NOT NULL,
    total_cents INTEGER NOT NULL, paid_cents INTEGER NOT NULL DEFAULT 0);
CREATE TABLE invoice_lines (invoice_id INTEGER NOT NULL, pos INTEGER NOT NULL,
    appt_id INTEGER NOT NULL, service_code TEXT NOT NULL, price_cents INTEGER NOT NULL,
    discount_cents INTEGER NOT NULL, net_cents INTEGER NOT NULL, tax_bp INTEGER NOT NULL,
    tax_cents INTEGER NOT NULL, total_cents INTEGER NOT NULL);
CREATE TABLE payments (id INTEGER PRIMARY KEY, invoice_id INTEGER NOT NULL,
    amount_cents INTEGER NOT NULL, method TEXT NOT NULL);
CREATE TABLE audit_log (seq INTEGER PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL,
    object TEXT NOT NULL, detail TEXT NOT NULL);
"""

TABLES = ("users", "roles", "role_parents", "role_rules", "customers", "services",
          "appointments", "invoices", "invoice_lines", "payments", "audit_log")


def connect(builtin_roles, first_user):
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for name, parents, grants, denies in builtin_roles:
        conn.execute("INSERT INTO roles VALUES (?, 1)", (name,))
        for pos, parent in enumerate(parents):
            conn.execute("INSERT INTO role_parents VALUES (?, ?, ?)", (name, parent, pos))
        for perm in grants:
            conn.execute("INSERT INTO role_rules VALUES (?, ?, 'grant')", (name, perm))
        for perm in denies:
            conn.execute("INSERT INTO role_rules VALUES (?, ?, 'deny')", (name, perm))
    conn.execute("INSERT INTO users VALUES (?, ?)", first_user)
    _track_writes(conn)
    return conn


def _track_writes(conn):
    """Count row writes per table in a TEMP table (not part of the schema).

    The counters live in the same transaction as the data, so the writes of
    a refused (rolled back) command disappear with it.
    """
    conn.execute("CREATE TEMP TABLE writes (tbl TEXT PRIMARY KEY, n INTEGER NOT NULL)")
    for table in TABLES:
        conn.execute("INSERT INTO temp.writes VALUES (?, 0)", (table,))
        for event in ("INSERT", "UPDATE", "DELETE"):
            conn.execute(
                "CREATE TEMP TRIGGER w_%s_%s AFTER %s ON main.%s BEGIN "
                "UPDATE writes SET n = n + 1 WHERE tbl = '%s'; END"
                % (table, event.lower(), event, table, table))


def run(conn, sql, params=()):
    try:
        return conn.execute(sql, params)
    except sqlite3.Error as exc:
        raise DbError(str(exc)) from None


def begin(conn):
    conn.execute("SAVEPOINT cmd")


def commit(conn):
    conn.execute("RELEASE cmd")


def rollback(conn):
    conn.execute("ROLLBACK TO cmd")
    conn.execute("RELEASE cmd")


def insert_record(conn, table, record):
    """INSERT one row.  TABLE and the keys of RECORD are program constants."""
    cols = list(record)
    sql = "INSERT INTO %s (%s) VALUES (%s)" % (
        table, ", ".join(cols), ", ".join("?" for _ in cols))
    return run(conn, sql, [record[c] for c in cols]).lastrowid


# ---------------------------------------------------------------- snapshots

def schema_text(conn):
    rows = conn.execute("SELECT type, name, sql FROM sqlite_master ORDER BY name").fetchall()
    return "\n".join("%s %s %s" % tuple(r) for r in rows)


def table_state(conn, table):
    """(row count, write counter) of TABLE; TABLE is one of TABLES."""
    count = conn.execute("SELECT count(*) FROM %s" % table).fetchone()[0]
    writes = conn.execute("SELECT n FROM temp.writes WHERE tbl = ?", (table,)).fetchone()[0]
    return count, writes


# ---------------------------------------------------------------- users and roles

def user_role(conn, name):
    row = run(conn, "SELECT role FROM users WHERE name = ?", (name,)).fetchone()
    return row["role"] if row else None


def add_user(conn, name, role):
    run(conn, "INSERT INTO users (name, role) VALUES (?, ?)", (name, role))


def role_row(conn, name):
    return run(conn, "SELECT name, builtin FROM roles WHERE name = ?", (name,)).fetchone()


def add_role(conn, name, parents):
    run(conn, "INSERT INTO roles (name, builtin) VALUES (?, 0)", (name,))
    for pos, parent in enumerate(parents):
        run(conn, "INSERT INTO role_parents (role, parent, pos) VALUES (?, ?, ?)",
            (name, parent, pos))


def role_parents(conn, name):
    rows = run(conn, "SELECT parent FROM role_parents WHERE role = ? ORDER BY pos", (name,))
    return [r["parent"] for r in rows]


def role_rules(conn, name):
    rows = run(conn, "SELECT perm, effect FROM role_rules WHERE role = ? ORDER BY rowid",
               (name,))
    return [(r["perm"], r["effect"]) for r in rows]


def add_rule(conn, role, perm, effect):
    run(conn, "INSERT INTO role_rules (role, perm, effect) VALUES (?, ?, ?)",
        (role, perm, effect))


# ---------------------------------------------------------------- customers

def add_customer(conn, name, phone, email, note):
    return run(conn, "INSERT INTO customers (name, phone, email, note) VALUES (?, ?, ?, ?)",
               (name, phone, email, note)).lastrowid


def customer(conn, cid):
    return run(conn, "SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()


def set_note(conn, cid, note):
    run(conn, "UPDATE customers SET note = ? WHERE id = ?", (note, cid))


def set_archived(conn, cid):
    run(conn, "UPDATE customers SET archived = 1 WHERE id = ?", (cid,))


def find_customers(conn, text):
    return run(conn, "SELECT * FROM customers WHERE instr(lower(name), lower(?)) > 0 "
                     "ORDER BY id", (text,)).fetchall()


def all_customers(conn):
    return run(conn, "SELECT * FROM customers ORDER BY id").fetchall()


# ---------------------------------------------------------------- services

def service(conn, code):
    return run(conn, "SELECT * FROM services WHERE code = ?", (code,)).fetchone()


def add_service(conn, code, name, minutes, price, tax_bp):
    run(conn, "INSERT INTO services (code, name, minutes, price_cents, tax_bp) "
              "VALUES (?, ?, ?, ?, ?)", (code, name, minutes, price, tax_bp))


def all_services(conn):
    return run(conn, "SELECT * FROM services ORDER BY code").fetchall()


# ---------------------------------------------------------------- appointments

def appointment(conn, aid):
    return run(conn, "SELECT * FROM appointments WHERE id = ?", (aid,)).fetchone()


def add_appointment(conn, cid, code, day, start, minutes):
    return run(conn, "INSERT INTO appointments (customer_id, service_code, day, start, minutes, "
                     "status) VALUES (?, ?, ?, ?, ?, 'booked')",
               (cid, code, day, start, minutes)).lastrowid


def set_status(conn, aid, status):
    run(conn, "UPDATE appointments SET status = ? WHERE id = ?", (status, aid))


def appointments_on(conn, day):
    return run(conn, "SELECT * FROM appointments WHERE day = ? ORDER BY start, id",
               (day,)).fetchall()


def active_on(conn, day):
    """Appointments that occupy the chair on DAY (booked or done)."""
    return run(conn, "SELECT * FROM appointments WHERE day = ? AND status IN ('booked', 'done') "
                     "ORDER BY start, id", (day,)).fetchall()


def booked_for(conn, cid):
    return run(conn, "SELECT * FROM appointments WHERE customer_id = ? AND status = 'booked' "
                     "ORDER BY day, start, id", (cid,)).fetchall()


def uninvoiced_done(conn, cid):
    return run(conn, """
        SELECT a.*, s.price_cents, s.tax_bp FROM appointments a
        JOIN services s ON s.code = a.service_code
        WHERE a.customer_id = ? AND a.status = 'done' AND NOT EXISTS (
            SELECT 1 FROM invoice_lines l JOIN invoices i ON i.id = l.invoice_id
            WHERE l.appt_id = a.id AND i.status != 'void')
        ORDER BY a.day, a.start, a.id""", (cid,)).fetchall()


def all_appointments(conn):
    return run(conn, """
        SELECT a.*, (SELECT l.invoice_id FROM invoice_lines l JOIN invoices i
                     ON i.id = l.invoice_id WHERE l.appt_id = a.id AND i.status != 'void')
               AS invoice_id
        FROM appointments a ORDER BY a.id""").fetchall()


# ---------------------------------------------------------------- invoices and payments

def add_invoice(conn, cid, discount_pct, net, tax, total):
    return run(conn, "INSERT INTO invoices (customer_id, status, discount_pct, net_cents, "
                     "tax_cents, total_cents) VALUES (?, 'open', ?, ?, ?, ?)",
               (cid, discount_pct, net, tax, total)).lastrowid


def add_line(conn, inv, pos, appt_id, code, price, discount, net, tax_bp, tax, total):
    run(conn, "INSERT INTO invoice_lines VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (inv, pos, appt_id, code, price, discount, net, tax_bp, tax, total))


def invoice(conn, inv):
    return run(conn, "SELECT * FROM invoices WHERE id = ?", (inv,)).fetchone()


def invoice_lines(conn, inv):
    return run(conn, "SELECT * FROM invoice_lines WHERE invoice_id = ? ORDER BY pos",
               (inv,)).fetchall()


def all_invoices(conn):
    return run(conn, "SELECT * FROM invoices ORDER BY id").fetchall()


def set_invoice_status(conn, inv, status):
    run(conn, "UPDATE invoices SET status = ? WHERE id = ?", (status, inv))


def add_payment(conn, inv, cents, method):
    pid = run(conn, "INSERT INTO payments (invoice_id, amount_cents, method) VALUES (?, ?, ?)",
              (inv, cents, method)).lastrowid
    run(conn, "UPDATE invoices SET paid_cents = paid_cents + ? WHERE id = ?", (cents, inv))
    return pid


def lines_in_range(conn, day_from, day_to):
    """Invoice lines of non-void invoices whose appointment day is in range."""
    return run(conn, """
        SELECT l.* FROM invoice_lines l
        JOIN invoices i ON i.id = l.invoice_id
        JOIN appointments a ON a.id = l.appt_id
        WHERE i.status != 'void' AND a.day BETWEEN ? AND ?
        ORDER BY l.invoice_id, l.pos""", (day_from, day_to)).fetchall()


def balances(conn):
    return run(conn, """
        SELECT c.id, c.name, SUM(i.total_cents) AS invoiced, SUM(i.paid_cents) AS paid
        FROM invoices i JOIN customers c ON c.id = i.customer_id
        WHERE i.status != 'void'
        GROUP BY c.id
        ORDER BY SUM(i.total_cents) - SUM(i.paid_cents) DESC, c.id""").fetchall()


# ---------------------------------------------------------------- audit log

def add_audit(conn, actor, action, obj, detail):
    run(conn, "INSERT INTO audit_log (actor, action, object, detail) VALUES (?, ?, ?, ?)",
        (actor, action, obj, detail))


def add_audit_many(conn, rows):
    try:
        conn.executemany("INSERT INTO audit_log (actor, action, object, detail) "
                         "VALUES (?, ?, ?, ?)", rows)
    except sqlite3.Error as exc:
        raise DbError(str(exc)) from None


def audit_rows(conn, limit=None):
    if limit is None:
        return run(conn, "SELECT * FROM audit_log ORDER BY seq").fetchall()
    rows = run(conn, "SELECT * FROM audit_log ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
    return list(reversed(rows))


def audit_since(conn, seq):
    return run(conn, "SELECT * FROM audit_log WHERE seq > ? ORDER BY seq", (seq,)).fetchall()


def last_audit_seq(conn):
    return run(conn, "SELECT COALESCE(MAX(seq), 0) FROM audit_log").fetchone()[0]
