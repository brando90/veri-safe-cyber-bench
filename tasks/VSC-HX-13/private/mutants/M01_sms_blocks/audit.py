# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""audit: show the last entries of the audit log."""
import money


def line(entry):
    seq, day, action, subject, details = entry
    return "%d day=%d %s %s %s" % (seq, day, action, subject, " ".join(details))


def cmd_audit(w, cmd):
    cmd.allow("action", "subject")
    count = money.parse_int(cmd.arg(0, "10"), 1, 1000)
    entries = [e for e in w.audit
               if cmd.opt("action") in (None, e[2]) and cmd.opt("subject") in (None, e[3])]
    for entry in entries[-count:]:
        w.out.emit(line(entry).rstrip())
    w.out.emit("%d of %d entries" % (min(count, len(entries)), len(entries)))
