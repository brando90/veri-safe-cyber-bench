# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Splitting a message body into fragments.

The body is UTF-8.  Each fragment carries at most ``frag.size_bytes`` bytes
and never ends inside a multi-byte character: the cut moves back to the
start of the character.  ``frag.size_bytes`` is at least 4 (config.KEYS),
the length of the longest UTF-8 character, so every fragment holds at least
one whole character.
"""

import model


def is_continuation(byte):
    return (byte & 0xC0) == 0x80


def split_bytes(data, limit):
    """Cut DATA into pieces of at most LIMIT bytes on character boundaries."""
    pieces = []
    start = 0
    n = len(data)
    while start < n:
        cut = min(start + limit, n)
        if cut < n:
            while is_continuation(data[cut]):
                cut -= 1
        pieces.append(data[start:cut])
        start = cut
    return pieces


def make_fragments(msg_id, body, limit):
    data = body.encode("utf-8")
    return [model.Fragment(msg_id, i + 1, piece)
            for i, piece in enumerate(split_bytes(data, limit))]


def count_fragments(body, limit):
    return len(split_bytes(body.encode("utf-8"), limit))
