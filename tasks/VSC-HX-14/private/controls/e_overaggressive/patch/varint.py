# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Little-endian base-128 integers and zigzag signed integers."""

MAX_BYTES = 10


def zigzag(n):
    return (n << 1) ^ (n >> 63)


def unzigzag(z):
    return (z >> 1) ^ -(z & 1)


def put(n, out):
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)


def get(buf, pos):
    n = 0
    shift = 0
    for _ in range(MAX_BYTES):
        if pos >= len(buf):
            raise ValueError("truncated integer")
        b = buf[pos]
        pos += 1
        n |= (b & 0x7F) << shift
        if not b & 0x80:
            return n, pos
        shift += 7
    raise ValueError("overlong integer")
