# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The audit log: one row per record created or changed.

Rows are written inside the command's savepoint, so a refused command leaves
no audit row.  The detail column uses the audit detail format from
formats.py (README, "Audit log").
"""

import formats
import parse
import store
from errors import CommandError

AUDIT_COLUMNS = ("seq", "actor", "action", "object", "detail")


def record(sess, action, obj, pairs):
    """Write one audit row; PAIRS is a list of (field, value)."""
    store.add_audit(sess.conn, sess.actor_name(), action, obj, formats.audit_detail(pairs))
    sess.expect.audit += 1


def record_many(sess, entries):
    """Write many audit rows at once.

    ENTRIES is a list of (action, object, detail) where DETAIL is already
    in the audit detail format.  Used by bulk operations.
    """
    actor = sess.actor_name()
    store.add_audit_many(sess.conn, [(actor, a, o, d) for a, o, d in entries])
    sess.expect.audit += len(entries)


def cmd_audit(sess, line):
    toks = parse.tokens(line)
    if len(toks) > 2:
        raise parse.usage("audit [N]")
    limit = parse.count(toks[1]) if len(toks) == 2 else None
    rows = store.audit_rows(sess.conn, limit)
    for r in rows:
        sess.emit("#%d %s %s %s %s" % (r["seq"], r["actor"], r["action"], r["object"],
                                       r["detail"]))
    sess.emit("entries: %d" % len(rows))


def cmd_export(sess, line):
    if len(parse.tokens(line)) != 1:
        raise CommandError("usage: audit-export")
    formats.emit_table(sess, "tsv", AUDIT_COLUMNS,
                       [[r[c] for c in AUDIT_COLUMNS] for r in store.audit_rows(sess.conn)])
