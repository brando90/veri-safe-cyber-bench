# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Report templates.

A template is one line of text with placeholders `{{field}}` or
`{{field|filter|filter:arg}}`.  It is rendered once per decision log entry.
Filters work on the plain value; the result is then escaped for the output
format of the report, so a template can be used for any format.  Literal
template text is written as it is.

Filters: upper, lower, trunc:N (keep the first N characters), default:WORD
(use WORD when the value is empty).
"""
import re

import escape
import limits
from errors import TemplateError

FIELDS = ("seq", "time", "set", "subject", "action", "resource", "effect", "by",
          "steps", "note", "context")
FILTERS = ("upper", "lower", "trunc", "default")
_PLACEHOLDER_RE = re.compile(r"\{\{([^{}]*)\}\}")
_NAME_RE = re.compile(limits.NAME_PATTERN)


class Template:
    def __init__(self, name, text, parts):
        self.name = name
        self.text = text
        self.parts = parts      # list of str (literal) or (field, [(filter, arg)])


def _parse_filter(text):
    name, sep, arg = text.partition(":")
    name = name.strip()
    if name not in FILTERS:
        raise TemplateError("unknown filter %s" % name)
    if name == "trunc":
        if not (sep and arg.isdigit() and 0 < int(arg) <= 200):
            raise TemplateError("trunc needs a length from 1 to 200")
        return (name, int(arg))
    if name == "default":
        if not sep or not arg:
            raise TemplateError("default needs a word")
        return (name, arg)
    if sep:
        raise TemplateError("%s takes no argument" % name)
    return (name, None)


def compile_template(name, text):
    if not _NAME_RE.fullmatch(name):
        raise TemplateError("bad template name %s" % name)
    if not text:
        raise TemplateError("empty template")
    if len(text) > limits.MAX_TEMPLATE_CHARS:
        raise TemplateError("template longer than %d characters" % limits.MAX_TEMPLATE_CHARS)
    parts = []
    pos = 0
    for m in _PLACEHOLDER_RE.finditer(text):
        if m.start() > pos:
            parts.append(text[pos:m.start()])
        pieces = m.group(1).split("|")
        field = pieces[0].strip()
        if field not in FIELDS:
            raise TemplateError("unknown field %s" % field)
        parts.append((field, [_parse_filter(p) for p in pieces[1:]]))
        pos = m.end()
    if pos < len(text):
        parts.append(text[pos:])
    if not any(isinstance(p, tuple) for p in parts):
        raise TemplateError("template has no placeholder")
    if any("{{" in p or "}}" in p for p in parts if isinstance(p, str)):
        raise TemplateError("unbalanced braces")
    return Template(name, text, parts)


def _apply(value, filters):
    for name, arg in filters:
        if name == "upper":
            value = value.upper()
        elif name == "lower":
            value = value.lower()
        elif name == "trunc":
            value = value[:arg]
        elif name == "default":
            value = value or arg
    return value


def render(tpl, fields, fmt):
    """Render TPL with FIELDS (plain, already redacted values) for FMT."""
    out = []
    for part in tpl.parts:
        if isinstance(part, str):
            out.append(part)
            continue
        field, filters = part
        out.append(escape.for_format(fmt, _apply(fields[field], filters)))
    return "".join(out)
