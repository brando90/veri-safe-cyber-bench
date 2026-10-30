# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Scrubbing of free-text messages."""
import re

import maskers

PAIR = r"\b(?:password|passwd|secret|token|apikey)=(\S+)"
TOKEN = r"\btok_[A-Za-z0-9]{8,}"


def _mask_pair(m):
    head = m.group(0)[: m.start(1) - m.start(0)]
    return head + maskers.partial(m.group(1))


def _mask_token(m):
    return maskers.partial(m.group(0))


def scrub(text):
    text = re.sub(PAIR, _mask_pair, text, re.IGNORECASE)
    text = re.sub(TOKEN, _mask_token, text)
    return text
