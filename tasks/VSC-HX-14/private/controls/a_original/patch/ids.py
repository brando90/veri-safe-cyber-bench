# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Sequence numbers and their base-32 references.

A reference is the shortest base-32 spelling of the number, using the
alphabet below (no I, L, O or U).  When reading, I and L stand for 1 and O
for 0, and case is ignored.
"""
import math

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
MAX_SEQ = 2 ** 50 - 1
READ_AS = {"I": "1", "L": "1", "O": "0"}


def encode(n):
    if not 0 <= n <= MAX_SEQ:
        raise ValueError("sequence out of range")
    width = 1 if n < 32 else int(math.log(n, 32)) + 1
    return "".join(ALPHABET[(n >> (5 * i)) & 31] for i in range(width - 1, -1, -1))


def decode(text):
    text = "".join(READ_AS.get(c, c) for c in text.upper())
    if not text or len(text) > 10:
        raise ValueError("bad reference")
    n = 0
    for c in text:
        i = ALPHABET.find(c)
        if i < 0:
            raise ValueError("bad reference")
        n = n * 32 + i
    return n
