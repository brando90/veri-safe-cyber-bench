# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""audit: the last entries of the audit log."""
import money
from errors import CommandError


def cmd_audit(w, cmd):
    cmd.allow("action", "subject")
    count = money.parse_int(cmd.arg(0, "10"), 1, 1000)
    action = cmd.opt("action")
    subject = cmd.opt("subject")
    rows = [e for e in w.audit
            if (action is None or e[2] == action) and (subject is None or e[3] == subject)]
    for seq, day, act, subj, details in rows[-count:]:
        w.out.emit("  #%d day %d %s %s %s" % (seq, day, act, subj, " ".join(details)))
    w.out.emit("%d entries" % len(rows))
