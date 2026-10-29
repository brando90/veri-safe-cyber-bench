# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""All SQL."""

import parse
import sqlite3
from errors import CommandError

cnx = None

def init(conn):
    global cnx
    cnx = conn
    with open("schema.sql") as f:
        conn.executescript(f.read())

def begin(conn):
    conn.execute("BEGIN")

def commit(conn):
    conn.commit()

def rollback(conn):
    conn.rollback()

def user_add(conn, user, role):
    try:
        conn.execute("INSERT INTO users (name, role) VALUES (?, ?)", (user, role))
    except sqlite3.IntegrityError:
        raise CommandError("duplicate-user: %s" % user)

def role_add(conn, role, parents):
    if role in BUILTIN_NAMES:
        raise CommandError("builtin-role: %s" % role)
    try:
        conn.execute("INSERT INTO roles (name) VALUES (?)", (role,))
    except sqlite3.IntegrityError:
        raise CommandError("duplicate-role: %s" % role)
    for parent in parents:
        conn.execute("INSERT INTO role_parents (child, parent) VALUES (?, ?)", (role, parent))

def role_rule(conn, role, effect, perm):
    if effect not in ("grant", "deny"):
        raise CommandError("unknown-perm: %s" % perm)
    if perm not in PERMS:
        raise CommandError("unknown-perm: %s" % perm)
    try:
        conn.execute("INSERT INTO role_rules (role, effect, perm) VALUES (?, ?, ?)", (role, effect, perm))
    except sqlite3.IntegrityError:
        raise CommandError("duplicate-rule: %s %s %s" % (role, effect, perm))

def user_row(conn, user):
    return conn.execute("SELECT * FROM users WHERE name = ?", (user,)).fetchone()

def role_row(conn, role):
    return conn.execute("SELECT * FROM roles WHERE name = ?", (role,)).fetchone()

def role_parents(conn, role):
    return [r[0] for r in conn.execute("SELECT parent FROM role_parents WHERE child = ?", (role,)).fetchall()]