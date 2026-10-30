# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Text cleaning and ordering helpers."""
import re
import unicodedata

from errors import CmdError

MAX_LABEL = 40
BLANK_RUN = re.compile(r"[ \t\r\n\f\v]+")
CHUNK_RE = re.compile(r"\d+|\D+")


def clean_label(text):
    text = unicodedata.normalize("NFC", text)
    return BLANK_RUN.sub(" ", text).strip(" ")


def check_label(text):
    label = clean_label(text)
    if not label:
        raise CmdError("empty label")
    if len(label) > MAX_LABEL:
        raise CmdError("label too long")
    if any(ord(ch) < 32 for ch in label):
        raise CmdError("bad character in label")
    return label


def fold(text):
    return text.casefold()


def natural_key(text):
    key = []
    for chunk in CHUNK_RE.findall(text):
        if chunk[0].isdigit():
            key.append((1, int(chunk), len(chunk)))
        else:
            key.append((0, 0, chunk))
    return key


def fit(text, width):
    """Pads or cuts text to exactly width characters; a cut ends in three dots."""
    if len(text) <= width:
        return text.ljust(width)
    return text[:width - 3] + "..."
