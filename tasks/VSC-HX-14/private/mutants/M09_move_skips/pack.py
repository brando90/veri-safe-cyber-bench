# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Binary form of an event and the checksummed frame that carries a batch.

Record: magic byte, then varints and length-prefixed UTF-8 strings (see
``pack_event``).  Frame: count, then each record length-prefixed; the
frame checksum is the Fletcher-16 of those bytes.
"""
import checksum
import rules
import varint
from errors import CommandError
from events import Event

MAGIC = 0xE1


def put_str(text, out):
    data = text.encode("utf-8")
    varint.put(len(data), out)
    out.extend(data)


def get_str(buf, pos):
    n, pos = varint.get(buf, pos)
    if pos + n > len(buf):
        raise ValueError("truncated string")
    return bytes(buf[pos:pos + n]).decode("utf-8"), pos + n


def pack_event(ev):
    out = bytearray([MAGIC])
    put_str(ev.id, out)
    varint.put(ev.seq, out)
    day, sod = divmod(ev.start, 86400)
    varint.put(varint.zigzag(day), out)
    varint.put(sod // 60, out)
    varint.put(ev.dur, out)
    varint.put(varint.zigzag(ev.tz), out)
    out.append((1 if ev.allday else 0) | (2 if ev.rule else 0))
    varint.put(ev.prio, out)
    varint.put(len(ev.cats), out)
    for c in ev.cats:
        put_str(c, out)
    put_str(ev.title, out)
    if ev.rule:
        put_str(ev.rule.text(), out)
    varint.put(len(ev.skips), out)
    prev = None
    for d in ev.skips:
        varint.put(varint.zigzag(d) if prev is None else d - prev, out)
        prev = d
    return bytes(out)


def unpack_event(buf):
    if not buf or buf[0] != MAGIC:
        raise ValueError("bad magic")
    pos = 1
    eid, pos = get_str(buf, pos)
    seq, pos = varint.get(buf, pos)
    z, pos = varint.get(buf, pos)
    minute, pos = varint.get(buf, pos)
    dur, pos = varint.get(buf, pos)
    tzz, pos = varint.get(buf, pos)
    flags = buf[pos]
    pos += 1
    prio, pos = varint.get(buf, pos)
    ncat, pos = varint.get(buf, pos)
    cats = []
    for _ in range(ncat):
        c, pos = get_str(buf, pos)
        cats.append(c)
    title, pos = get_str(buf, pos)
    rule = None
    if flags & 2:
        text, pos = get_str(buf, pos)
        rule = rules.parse(text)
    nskip, pos = varint.get(buf, pos)
    skips = []
    for i in range(nskip):
        n, pos = varint.get(buf, pos)
        skips.append(varint.unzigzag(n) if i == 0 else skips[-1] + n)
    if pos != len(buf):
        raise ValueError("trailing bytes")
    start = varint.unzigzag(z) * 86400 + minute * 60
    return Event(eid, seq, title, start, start, dur, rule, varint.unzigzag(tzz),
                 bool(flags & 1), prio, cats, skips)


def frame(events):
    out = bytearray()
    varint.put(len(events), out)
    for ev in events:
        rec = pack_event(ev)
        varint.put(len(rec), out)
        out.extend(rec)
    return bytes(out), checksum.fletcher16(out)


def unframe(data, total):
    if checksum.fletcher16(data) != total:
        raise CommandError("bad_checksum")
    try:
        n, pos = varint.get(data, 0)
        out = []
        for _ in range(n):
            size, pos = varint.get(data, pos)
            if pos + size > len(data):
                raise ValueError("truncated record")
            out.append(unpack_event(data[pos:pos + size]))
            pos += size
        if pos != len(data):
            raise ValueError("trailing bytes")
    except (ValueError, IndexError, CommandError, UnicodeDecodeError):
        raise CommandError("bad_record", "pack") from None
    return out
