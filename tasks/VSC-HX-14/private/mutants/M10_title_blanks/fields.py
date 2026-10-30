# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Text escaping for stored records, the category list codec and titles.

A record field never contains a raw ``|``.  Inside a category list a raw
comma separates items.  A backslash starts an escape in both.
"""
import re

from errors import CommandError

FIELD_ESC = {"\\": "\\\\", "|": "\\p", "\t": "\\t"}
FIELD_UNESC = {"\\": "\\", "p": "|", "t": "\t"}
MAX_TITLE = 80
MAX_CATS = 8
MAX_CAT_LEN = 24


def esc(text):
    return "".join(FIELD_ESC.get(c, c) for c in text)


def unesc(text):
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c != "\\":
            out.append(c)
            i += 1
            continue
        if i + 1 >= len(text) or text[i + 1] not in FIELD_UNESC:
            raise ValueError("bad escape")
        out.append(FIELD_UNESC[text[i + 1]])
        i += 2
    return "".join(out)


def esc_item(item):
    return item.replace("\\", "\\\\").replace(",", "\\,")


def join_list(items):
    return ",".join(esc_item(i) for i in items)


def split_list(text):
    if text == "":
        return []
    items = []
    cur = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text):
            cur.append(text[i + 1])
            i += 2
        elif c == ",":
            items.append("".join(cur))
            cur = []
            i += 1
        else:
            cur.append(c)
            i += 1
    items.append("".join(cur))
    return items


def normalize_title(text):
    text = re.sub(r"\t", " ", text.strip(" \t"))
    return text.replace("  ", " ")


def clean_title(text):
    title = normalize_title(text)
    if not title or len(title) > MAX_TITLE or any(ord(c) < 32 or ord(c) == 127 for c in title):
        raise CommandError("bad_title", text)
    return title


def clean_cats(text):
    items = split_list(text)
    out = []
    for item in items:
        if not item or len(item) > MAX_CAT_LEN or any(ord(c) < 32 or ord(c) == 127 for c in item):
            raise CommandError("bad_cats", text)
        if item not in out:
            out.append(item)
    if len(out) > MAX_CATS:
        raise CommandError("bad_cats", text)
    return out
