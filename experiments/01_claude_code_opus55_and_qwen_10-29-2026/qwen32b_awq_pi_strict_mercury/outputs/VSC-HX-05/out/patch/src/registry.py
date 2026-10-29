# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The command table and the per-line dispatcher.

For every command line the dispatcher:
  1. reads the command's data block (import) if it has one;
  2. takes the consistency-check snapshot and opens a savepoint;
  3. checks the permissions listed for the command, in order;
  4. runs the handler, which validates its arguments, checks any further
     permissions and makes the change;
  5. on CommandError rolls back and prints "ERROR ...", otherwise commits
     and prints the handler's output;
  6. runs the consistency check.
"""

import admin
import appointments
import audit
import billing
import customers
import invariant
import parse
import reports
import store
import transfer
from errors import CommandError


class Cmd:
    def __init__(self, handler, perms=(), block=False):
        self.handler = handler
        self.perms = perms
        self.block = block


COMMANDS = {
    "as": Cmd(admin.cmd_as),
    "whoami": Cmd(admin.cmd_whoami),
    "perms": Cmd(admin.cmd_perms),
    "user-add": Cmd(admin.cmd_user_add, ("user.manage",)),
    "role-add": Cmd(admin.cmd_role_add, ("role.manage",)),
    "role-grant": Cmd(admin.cmd_role_grant, ("role.manage",)),
    "role-deny": Cmd(admin.cmd_role_deny, ("role.manage",)),
    "customer-add": Cmd(customers.cmd_add, ("customer.write",)),
    "customer-note": Cmd(customers.cmd_note, ("customer.write",)),
    "customer-show": Cmd(customers.cmd_show, ("customer.view",)),
    "customer-find": Cmd(customers.cmd_find, ("customer.view",)),
    "customer-archive": Cmd(customers.cmd_archive, ("customer.write", "appt.cancel")),
    "service-add": Cmd(appointments.cmd_service_add, ("service.write",)),
    "services": Cmd(appointments.cmd_services, ("appt.view",)),
    "book": Cmd(appointments.cmd_book, ("appt.write",)),
    "appt-status": Cmd(appointments.cmd_status, ("appt.write",)),
    "cancel": Cmd(appointments.cmd_cancel, ("appt.cancel",)),
    "appts": Cmd(appointments.cmd_appts, ("appt.view",)),
    "invoice-create": Cmd(billing.cmd_invoice_create, ("invoice.write",)),
    "invoice-show": Cmd(billing.cmd_invoice_show, ("invoice.view",)),
    "pay": Cmd(billing.cmd_pay, ("payment.record",)),
    "invoice-void": Cmd(billing.cmd_invoice_void, ("invoice.void",)),
    "report": Cmd(reports.cmd_report, ("report.view",)),
    "export": Cmd(transfer.cmd_export, ("export.run",)),
    "import": Cmd(transfer.cmd_import, ("import.run",), block=True),
    "audit": Cmd(audit.cmd_audit, ("audit.view",)),
    "audit-export": Cmd(audit.cmd_export, ("audit.view", "export.run")),
}


def read_block(sess):
    """Lines up to '.end' as [(n, text)] (n counts from 1), and whether '.end' was seen."""
    block = []
    for raw in sess.lines:
        if raw.strip(parse.BLANKS) == ".end":
            return block, True
        block.append((len(block) + 1, raw))
    return block, False


def run_line(sess, line):
    toks = parse.tokens(line)
    if not toks or toks[0].startswith("#"):
        return
    cmd = COMMANDS.get(toks[0])
    if cmd is None:
        sess.out.write("ERROR unknown-command: %s\n" % toks[0])
        return
    block, complete = read_block(sess) if cmd.block else (None, True)
    conn = sess.conn
    expect = invariant.Expect(conn)
    sess.expect = expect
    store.begin(conn)
    try:
        for perm in cmd.perms:
            sess.require(perm)
        if cmd.block:
            if not complete:
                raise CommandError("import: missing .end")
            cmd.handler(sess, line, block)
        else:
            cmd.handler(sess, line)
    except CommandError as exc:
        store.rollback(conn)
        expect.reset()
        sess.discard()
        sess.emit("ERROR %s" % exc)
    else:
        store.commit(conn)
    sess.flush()
    invariant.check(sess, expect)