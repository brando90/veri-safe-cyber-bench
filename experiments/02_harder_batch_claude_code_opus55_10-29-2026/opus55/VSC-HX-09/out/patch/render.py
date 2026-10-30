# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Decision reports and log listings.

Built-in layouts exist for the four formats; a named template can be used
instead (one line per entry, no header or summary).  Field values are
taken from the log as plain text, redacted, and escaped exactly once where
they are placed into the output.
"""
import escape
import numfmt
import redact
import template
from errors import TemplateError, UsageError

COLUMNS = template.FIELDS


def _context(entry, fmt):
    pairs = ["%s=%s" % (key, entry.attrs[key]) for key in sorted(entry.attrs)]
    return "; ".join(pairs)


def _fields(sess, entry, fmt):
    """Plain (unescaped, unredacted) field values of one entry."""
    note = entry.note
    if not note and fmt in ("text", "html"):
        note = "-"
    return {
        "seq": str(entry.seq),
        "time": str(entry.time),
        "set": entry.set_name,
        "subject": entry.subject,
        "action": entry.action,
        "resource": entry.resource,
        "effect": entry.effect,
        "by": entry.by,
        "steps": str(entry.steps),
        "note": note,
        "context": _context(entry, fmt),
    }


def text_line(sess, entry):
    f = _fields(sess, entry, "text")
    line = "#%s t=%s %s %s %s %s -> %s by=%s steps=%s" % (
        f["seq"], f["time"], f["set"], f["subject"], f["action"], f["resource"],
        f["effect"], f["by"], f["steps"])
    if f["note"] != "-":
        line += " note: " + f["note"]
    if f["context"]:
        line += " [" + f["context"] + "]"
    # text output has no escaping, so the finished line can be redacted
    return redact.scrub(sess, line)


def _summary(entries):
    total = len(entries)
    allowed = sum(1 for e in entries if e.effect == "allow")
    pct = numfmt.pct1(allowed, total) if total else "-"
    return total, allowed, pct


def _text_report(sess, entries):
    lines = [text_line(sess, e) for e in entries]
    total, _, pct = _summary(entries)
    lines.append("-- %s, %s%% allowed" % (numfmt.plural(total, "decision"), pct))
    return lines


def _json_report(sess, entries):
    lines = []
    for e in entries:
        f = redact.scrub_all(sess, _fields(sess, e, "json"))
        pairs = []
        for col in COLUMNS:
            if col in ("seq", "time", "steps"):
                pairs.append((col, int(f[col])))
            else:
                pairs.append((col, f[col]))
        lines.append(escape.json_object(pairs))
    total, _, pct = _summary(entries)
    lines.append(escape.json_object([("decisions", total), ("allowed_pct", pct)]))
    return lines


def _csv_report(sess, entries):
    lines = [",".join(COLUMNS)]
    for e in entries:
        f = redact.scrub_all(sess, _fields(sess, e, "csv"))
        lines.append(",".join(escape.csv_field(f[c]) for c in COLUMNS))
    return lines


def _html_cell(column, value):
    return "<td class=\"%s\">%s</td>" % (column, escape.html(value))


def _html_report(sess, entries):
    lines = ['<table class="decisions">',
             "<tr>" + "".join("<th>%s</th>" % c for c in COLUMNS) + "</tr>"]
    for e in entries:
        f = redact.scrub_all(sess, _fields(sess, e, "html"))
        row = "".join(_html_cell(c, f[c]) for c in COLUMNS)
        lines.append("<tr>" + row + "</tr>")
    total, _, pct = _summary(entries)
    lines.append('<tr class="summary"><td colspan="%d">%s, %s%% allowed</td></tr>' % (
        len(COLUMNS), numfmt.plural(total, "decision"), pct))
    lines.append("</table>")
    return lines


def _template_report(sess, entries, tpl, fmt):
    lines = []
    for e in entries:
        f = redact.scrub_all(sess, _fields(sess, e, fmt))
        lines.append(template.render(tpl, f, fmt, lambda text: redact.scrub(sess, text)))
    return lines


LAYOUTS = {
    "text": _text_report,
    "json": _json_report,
    "csv": _csv_report,
    "html": _html_report,
}


def report(sess, fmt, template_name=None):
    if fmt not in LAYOUTS:
        raise UsageError("unknown format %s" % fmt)
    entries = sess.log.ordered()
    if template_name is not None:
        tpl = sess.templates.get(template_name)
        if tpl is None:
            raise TemplateError("unknown template %s" % template_name)
        return _template_report(sess, entries, tpl, fmt)
    return LAYOUTS[fmt](sess, entries)
