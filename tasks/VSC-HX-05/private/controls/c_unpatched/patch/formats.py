# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Machine-readable text formats: CSV, TSV and audit details.

These are the only places that know the escaping rules (README, "Output
formats").  Anything that writes CSV, TSV or an audit detail goes through
here, so a value can never be mistaken for a separator.
"""

from errors import CommandError

# ---------------------------------------------------------------- CSV

CSV_SPECIAL = (",", '"', "\r", "\n")


def csv_field(value):
    s = str(value)
    if any(c in s for c in CSV_SPECIAL):
        return '"' + s.replace('"', '""') + '"'
    return s


def csv_line(values):
    return ",".join(csv_field(v) for v in values)


# ---------------------------------------------------------------- TSV

TSV_ESCAPES = {"\\": "\\\\", "\t": "\\t", "\n": "\\n", "\r": "\\r"}
TSV_UNESCAPES = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}


def tsv_field(value):
    return "".join(TSV_ESCAPES.get(c, c) for c in str(value))


def tsv_line(values):
    return "\t".join(tsv_field(v) for v in values)


def tsv_decode(field):
    """Undo tsv_field.  Raises ValueError on an unknown escape."""
    out = []
    i = 0
    while i < len(field):
        c = field[i]
        if c == "\\":
            if i + 1 >= len(field) or field[i + 1] not in TSV_UNESCAPES:
                raise ValueError("bad escape")
            out.append(TSV_UNESCAPES[field[i + 1]])
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def tsv_split(line):
    return [tsv_decode(f) for f in line.split("\t")]


def emit_table(sess, fmt, header, rows):
    """Write HEADER and ROWS as a CSV or TSV document."""
    line = csv_line if fmt == "csv" else tsv_line
    sess.emit(line(header))
    for row in rows:
        sess.emit(line(row))


# ---------------------------------------------------------------- audit details

AUDIT_ESCAPES = {"\\": "\\\\", '"': '\\"', "\t": "\\t", "\n": "\\n", "\r": "\\r"}
AUDIT_UNESCAPES = {"\\": "\\", '"': '"', "t": "\t", "n": "\n", "r": "\r"}


def audit_value(value):
    return "".join(AUDIT_ESCAPES.get(c, c) for c in str(value))


def audit_detail(pairs):
    """[('name', 'Ann'), ('phone', '555')] -> 'name="Ann" phone="555"'."""
    return " ".join('%s="%s"' % (key, audit_value(val)) for key, val in pairs)


def parse_audit_detail(text):
    """Strict inverse of audit_detail; raises ValueError if malformed."""
    pairs = []
    i, n = 0, len(text)
    while i < n:
        j = text.find('="', i)
        if j <= i:
            raise ValueError("expected key")
        key = text[i:j]
        if not key.replace("_", "").isalnum():
            raise ValueError("bad key")
        i = j + 2
        val = []
        while True:
            if i >= n:
                raise ValueError("unterminated value")
            c = text[i]
            if c == '"':
                i += 1
                break
            if c == "\\":
                if i + 1 >= n or text[i + 1] not in AUDIT_UNESCAPES:
                    raise ValueError("bad escape")
                val.append(AUDIT_UNESCAPES[text[i + 1]])
                i += 2
                continue
            if c in "\t\r\n":
                raise ValueError("raw control character")
            val.append(c)
            i += 1
        pairs.append((key, "".join(val)))
        if i < n:
            if text[i] != " ":
                raise ValueError("expected space")
            i += 1
            if i >= n:
                raise ValueError("trailing space")
    return pairs


def check_fmt(fmt, usage_text):
    if fmt not in ("csv", "tsv"):
        raise CommandError("usage: " + usage_text)
    return fmt
