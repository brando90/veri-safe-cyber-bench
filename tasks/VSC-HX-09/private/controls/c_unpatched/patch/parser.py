# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Recursive-descent parser of the condition language.

Grammar (lowest precedence first):
  expr    := and ("or" and)*
  and     := not ("and" not)*
  not     := "not" not | cmp
  cmp     := primary [(OP | "in") primary]
  primary := NUM | STR | true | false | NAME | NAME "(" args ")"
           | "@" name | "(" expr ")" | "[" args "]"

AST nodes are tuples whose first item is the node kind:
  ("num", n) ("str", s) ("bool", b) ("name", dotted) ("list", [items])
  ("not", x) ("and", a, b) ("or", a, b) ("cmp", op, a, b) ("in", a, b)
  ("call", fname, [args]) ("macro", name)

Every kind of nesting (parentheses, not, list literals and call arguments)
counts towards the single depth limit, so evaluation never recurses deeper
than the parser allowed.
"""
import limits
import lexer
from errors import ParseError

# name -> number of arguments
FUNCTIONS = {
    "len": 1,
    "lower": 1,
    "upper": 1,
    "startswith": 2,
    "glob": 2,
    "any_glob": 2,
    "count": 2,
    "hours": 1,
    "minutes": 1,
}


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0
        self.depth = 0

    # -- token helpers ---------------------------------------------------
    def peek(self):
        return self.toks[self.i]

    def take(self):
        tok = self.toks[self.i]
        self.i += 1
        return tok

    def at(self, kind, value=None):
        tok = self.toks[self.i]
        return tok[0] == kind and (value is None or tok[1] == value)

    def expect(self, kind, value):
        tok = self.take()
        if tok[0] != kind or tok[1] != value:
            raise ParseError("expected %s at column %d" % (value, tok[2]))
        return tok

    def _enter(self):
        self.depth += 1
        if self.depth > limits.MAX_DEPTH:
            raise ParseError("expression nested deeper than %d" % limits.MAX_DEPTH)

    def _leave(self):
        self.depth -= 1

    # -- grammar -----------------------------------------------------------
    def parse(self):
        node = self._or()
        tok = self.peek()
        if tok[0] != "END":
            raise ParseError("unexpected %s at column %d" % (_show(tok), tok[2]))
        return node

    def _or(self):
        left = self._and()
        while self.at("KW", "or"):
            self.take()
            left = ("or", left, self._and())
        return left

    def _and(self):
        left = self._not()
        while self.at("KW", "and"):
            self.take()
            left = ("and", left, self._not())
        return left

    def _not(self):
        if self.at("KW", "not"):
            self.take()
            self._enter()
            try:
                return ("not", self._not())
            finally:
                self._leave()
        return self._cmp()

    def _cmp(self):
        left = self._primary()
        if self.at("OP"):
            op = self.take()[1]
            right = self._primary()
            node = ("cmp", op, left, right)
        elif self.at("KW", "in"):
            self.take()
            node = ("in", left, self._primary())
        else:
            return left
        if self.at("OP") or self.at("KW", "in"):
            tok = self.peek()
            raise ParseError("comparisons cannot be chained (column %d)" % tok[2])
        return node

    def _primary(self):
        tok = self.take()
        kind, value, col = tok
        if kind == "NUM":
            return ("num", value)
        if kind == "STR":
            return ("str", value)
        if kind == "KW" and value in ("true", "false"):
            return ("bool", value == "true")
        if kind == "MACRO":
            return ("macro", value)
        if kind == "NAME":
            if self.at("PUNCT", "("):
                return self._call(value, col)
            return ("name", value)
        if kind == "PUNCT" and value == "(":
            self._enter()
            try:
                node = self._or()
                self.expect("PUNCT", ")")
                return node
            finally:
                self._leave()
        if kind == "PUNCT" and value == "[":
            return self._list()
        raise ParseError("unexpected %s at column %d" % (_show(tok), col))

    def _call(self, fname, col):
        if fname not in FUNCTIONS:
            raise ParseError("unknown function %s at column %d" % (fname, col))
        self.take()  # "("
        self._enter()
        try:
            args = self._items(")")
        finally:
            self._leave()
        if len(args) != FUNCTIONS[fname]:
            raise ParseError("%s takes %d argument%s" % (
                fname, FUNCTIONS[fname], "" if FUNCTIONS[fname] == 1 else "s"))
        return ("call", fname, args)

    def _list(self):
        items = self._items("]")
        if len(items) > limits.MAX_LIST_ITEMS:
            raise ParseError("list literal longer than %d items" % limits.MAX_LIST_ITEMS)
        return ("list", items)

    def _items(self, closer):
        items = []
        if self.at("PUNCT", closer):
            self.take()
            return items
        while True:
            items.append(self._or())
            if self.at("PUNCT", ","):
                self.take()
                continue
            self.expect("PUNCT", closer)
            return items


def _show(tok):
    if tok[0] == "END":
        return "end of expression"
    if tok[0] == "STR":
        return "string"
    return repr(str(tok[1]))


def parse_expr(text):
    text = text.strip()
    if not text:
        raise ParseError("empty expression")
    return Parser(lexer.tokenize(text)).parse()


def macro_refs(node, out=None):
    """Names of the named conditions (@name) an AST refers to, in order."""
    if out is None:
        out = []
    kind = node[0]
    if kind == "macro":
        if node[1] not in out:
            out.append(node[1])
    elif kind == "list":
        for item in node[1]:
            macro_refs(item, out)
    elif kind == "call":
        for item in node[2]:
            macro_refs(item, out)
    elif kind in ("not",):
        macro_refs(node[1], out)
    elif kind in ("and", "or", "in"):
        macro_refs(node[1], out)
        macro_refs(node[2], out)
    elif kind == "cmp":
        macro_refs(node[2], out)
        macro_refs(node[3], out)
    return out


def node_count(node):
    kind = node[0]
    if kind == "list":
        return 1 + sum(node_count(x) for x in node[1])
    if kind == "call":
        return 1 + sum(node_count(x) for x in node[2])
    if kind == "not":
        return 1 + node_count(node[1])
    if kind in ("and", "or", "in"):
        return 1 + node_count(node[1]) + node_count(node[2])
    if kind == "cmp":
        return 1 + node_count(node[2]) + node_count(node[3])
    return 1
