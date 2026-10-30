# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Tab-separated text records."""

ESCAPE_MAP = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r"}


def esc(text):
    return (text.replace("\\", "\\\\").replace("\t", "\\t")
            .replace("\n", "\\n").replace("\r", "\\r"))


def unesc(text):
    out = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in ESCAPE_MAP:
            out.append(ESCAPE_MAP[text[i + 1]])
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def row(fields):
    return "\t".join(str(f) for f in fields)


def erow(fields):
    return row([esc(str(f)) for f in fields])


def split_row(line):
    return [unesc(part) for part in line.split("\t")]
