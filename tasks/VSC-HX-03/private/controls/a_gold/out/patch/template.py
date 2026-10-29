# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The template language.

    {{ name }}                 value of a variable ('' if unknown)
    {{ name|upper|escape }}    with filters: upper, lower, trim, escape
    {% include "NAME" %}       text of src/NAME, rendered with the same variables
    {% asset "NAME" %}         URL of an asset below src/assets (assets.py)
    {% if name %} ... {% else %} ... {% endif %}

Include and asset names may contain {{ ... }} expressions, which are replaced
before the name is used. Tags never span lines. Everything else is copied
unchanged, including whitespace.
"""

import html
import re

import assets
import sitepath
from errors import SiteError

TAG = re.compile(r"\{\{(.*?)\}\}|\{%(.*?)%\}")
EXPR = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*)((?:\s*\|\s*[a-z]+)*)\s*\Z")
QUOTED = re.compile(r'\s*(include|asset)\s+"([^"]*)"\s*\Z')
IF_TAG = re.compile(r"\s*if\s+([A-Za-z_][A-Za-z0-9_]*)\s*\Z")
MAX_INCLUDE_DEPTH = 8

FILTERS = {
    "upper": str.upper,
    "lower": str.lower,
    "trim": str.strip,
    "escape": lambda value: html.escape(value, quote=True),
}


class Text:
    def __init__(self, text):
        self.text = text


class Var:
    def __init__(self, name, filters):
        self.name = name
        self.filters = filters


class Include:
    def __init__(self, name, location):
        self.name = name
        # resolved at parse time for names without expressions; None otherwise
        self.location = location


class Asset:
    def __init__(self, name):
        self.name = name


class If:
    def __init__(self, name):
        self.name = name
        self.then = []
        self.otherwise = []


def _parse_expr(body):
    match = EXPR.match(body)
    if match is None:
        return None
    filters = [f.strip() for f in match.group(2).split("|")[1:]]
    if any(f not in FILTERS for f in filters):
        return None
    return Var(match.group(1), filters)


def evaluate(var, variables):
    value = variables.get(var.name, "")
    for name in var.filters:
        value = FILTERS[name](value)
    return value


def substitute(text, variables):
    """Replace every {{ ... }} in ``text`` (used for include and asset names)."""
    def repl(match):
        var = _parse_expr(match.group(1))
        if var is None:
            raise SiteError("bad template")
        return evaluate(var, variables)
    return re.sub(r"\{\{(.*?)\}\}", repl, text)


class Parser:
    """Turns template text into a node list."""

    def __init__(self, tenant):
        self.tenant = tenant

    def parse(self, text):
        root = []
        stack = [(None, root)]          # (If node or None, list being filled)
        pos = 0
        for match in TAG.finditer(text):
            if match.start() > pos:
                stack[-1][1].append(Text(text[pos:match.start()]))
            pos = match.end()
            if match.group(1) is not None:
                var = _parse_expr(match.group(1))
                if var is None:
                    raise SiteError("bad template")
                stack[-1][1].append(var)
                continue
            body = match.group(2)
            word = body.strip()
            quoted = QUOTED.match(body)
            cond = IF_TAG.match(body)
            if quoted and quoted.group(1) == "include":
                name = quoted.group(2)
                location = None
                if "{{" not in name:
                    location = self.tenant.locate(self.tenant.src, name)
                stack[-1][1].append(Include(name, location))
            elif quoted:
                stack[-1][1].append(Asset(quoted.group(2)))
            elif cond:
                node = If(cond.group(1))
                stack[-1][1].append(node)
                stack.append((node, node.then))
            elif word == "else":
                node = stack[-1][0]
                if node is None or stack[-1][1] is node.otherwise:
                    raise SiteError("bad template")
                stack[-1] = (node, node.otherwise)
            elif word == "endif":
                if stack[-1][0] is None:
                    raise SiteError("bad template")
                stack.pop()
            else:
                raise SiteError("bad template")
        if len(stack) != 1:
            raise SiteError("bad template")
        if pos < len(text):
            root.append(Text(text[pos:]))
        return root


class Renderer:
    """Renders templates for one tenant; every file read is recorded in ``deps``."""

    def __init__(self, tenant, deps):
        self.tenant = tenant
        self.deps = deps
        self.parser = Parser(tenant)
        self._parsed = {}

    def render_text(self, text, variables):
        out = []
        self._run(self.parser.parse(text), variables, out, 0)
        return "".join(out)

    def _file_nodes(self, real):
        nodes = self._parsed.get(real)
        if nodes is None:
            text = self.tenant.read_text(real)
            self.deps.record(real, text)
            nodes = self.parser.parse(text)
            self._parsed[real] = nodes
        return nodes

    def _run(self, nodes, variables, out, depth):
        for node in nodes:
            if isinstance(node, Text):
                out.append(node.text)
            elif isinstance(node, Var):
                out.append(evaluate(node, variables))
            elif isinstance(node, If):
                branch = node.then if variables.get(node.name, "") else node.otherwise
                self._run(branch, variables, out, depth)
            elif isinstance(node, Include):
                self._include(node, variables, out, depth)
            elif isinstance(node, Asset):
                name = substitute(node.name, variables)
                out.append(assets.url_for(self.tenant, name, self.deps))

    def _include(self, node, variables, out, depth):
        if depth >= MAX_INCLUDE_DEPTH:
            raise SiteError("include too deep")
        real = node.location
        if real is None:
            name = substitute(node.name, variables)
            real = self.tenant.locate(self.tenant.src, name)
        self._run(self._file_nodes(real), variables, out, depth + 1)
