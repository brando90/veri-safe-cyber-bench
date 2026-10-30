# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Export and import: text records and checksummed pack frames."""
import durations
import expand
import fields
import ids
import names
import pack
import textrec
from errors import CommandError


def cmd_export_text(w, cmd):
    rows = w.store.ordered()
    for ev in rows:
        w.emit(textrec.format_record(ev))
    w.emit("# %d events" % len(rows))


def cmd_export_pack(w, cmd):
    data, total = pack.frame(w.store.ordered())
    w.emit("pack %04x %s" % (total, data.hex()))


def check_imported(w, ev):
    """Refuse imported events that break the rules commands keep."""
    try:
        names.check_id(ev.id)
        if ev.seq > ids.MAX_SEQ or ev.id in w.store.by_id or ev.seq in w.store.by_seq:
            raise ValueError("identity")
        if fields.clean_title(ev.title) != ev.title:
            raise ValueError("title")
        if fields.clean_cats(fields.join_list(ev.cats)) != ev.cats:
            raise ValueError("cats")
        if ev.dur > durations.MAX_SECONDS or ev.prio > 9:
            raise ValueError("range")
        step = 86400 if ev.allday else 60
        if ev.start % step or abs(ev.raw - ev.start) > 30:
            raise ValueError("start")
        if ev.skips != sorted(set(ev.skips)) or (ev.skips and ev.rule is None):
            raise ValueError("skips")
        if ev.skips:
            live = set(expand.between(ev, ev.skips[0], ev.skips[-1], with_skips=True))
            if not set(ev.skips) <= live:
                raise ValueError("skips")
    except (ValueError, CommandError):
        raise CommandError("bad_record", ev.id) from None


def adopt(w, batch):
    seen_ids = set()
    seen_seqs = set()
    for ev in batch:
        check_imported(w, ev)
        if ev.id in seen_ids or ev.seq in seen_seqs:
            raise CommandError("event_exists", ev.id)
        seen_ids.add(ev.id)
        seen_seqs.add(ev.seq)
    for ev in batch:
        w.store.insert(ev)
    w.emit("imported %d events" % len(batch))


def cmd_import_rec(w, cmd):
    adopt(w, [textrec.parse_record(cmd.arg(0))])


def cmd_import_pack(w, cmd):
    try:
        total = int(cmd.arg(0), 16)
        data = bytes.fromhex(cmd.arg(1))
    except ValueError:
        raise CommandError("bad_hex") from None
    adopt(w, pack.unframe(data, total))


def cmd_idseq(w, cmd):
    text = cmd.arg(0)
    if not text.isdigit() or int(text) > ids.MAX_SEQ:
        raise CommandError("bad_number", text)
    n = int(text)
    if n < w.store.next_seq:
        raise CommandError("seq_too_low", n, w.store.next_seq)
    w.store.next_seq = n
    w.emit("next sequence is %d (%s)" % (n, ids.encode(n)))
