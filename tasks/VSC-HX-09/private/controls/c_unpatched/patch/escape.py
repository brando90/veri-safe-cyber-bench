# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Escaping rules of the output formats.

text  values are printed as they are
json  string content: \\ and " are backslash-escaped, newline/TAB/CR as
      \\n \\t \\r, other control characters as \\u00XX; everything else,
      including non-ASCII letters and /, is written as is (UTF-8)
html  & < > " ' become &amp; &lt; &gt; &quot; &#39;
csv   a field is enclosed in double quotes when it contains a comma, a
      double quote, CR or LF, or starts or ends with a space; inner double
      quotes are doubled
"""

_JSON_SPECIAL = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\t": "\\t", "\r": "\\r"}
_HTML_SPECIAL = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}

FORMATS = ("text", "json", "html", "csv")


def json_inner(text):
    out = []
    for ch in text:
        if ch in _JSON_SPECIAL:
            out.append(_JSON_SPECIAL[ch])
        elif ord(ch) < 0x20:
            out.append("\\u%04x" % ord(ch))
        else:
            out.append(ch)
    return "".join(out)


def json_str(text):
    return '"' + json_inner(text) + '"'


def html(text):
    return "".join(_HTML_SPECIAL.get(ch, ch) for ch in text)


def csv_field(text):
    if text == "":
        return text
    needs = any(ch in text for ch in ',"\r\n') or text[0] == " " or text[-1] == " "
    if not needs:
        return text
    return '"' + text.replace('"', '""') + '"'


def for_format(fmt, text):
    """Escape one value for placement into output of format FMT."""
    if fmt == "json":
        return json_inner(text)
    if fmt == "html":
        return html(text)
    if fmt == "csv":
        return csv_field(text)
    return text


def json_object(pairs):
    """One-line JSON object from (key, value) pairs; values are str or int."""
    parts = []
    for key, value in pairs:
        if isinstance(value, int):
            parts.append("%s:%d" % (json_str(key), value))
        else:
            parts.append("%s:%s" % (json_str(key), json_str(value)))
    return "{" + ",".join(parts) + "}"
