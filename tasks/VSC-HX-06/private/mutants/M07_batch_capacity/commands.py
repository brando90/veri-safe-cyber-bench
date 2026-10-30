# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Command handlers and the command table."""

import billing
import config
import doctor
import explain
import export
import helptext
import intake
import invariant
import forecast
import latency
import lexer
import link
import report
import snapshot
import stats
import timefmt
from errors import CommandError
from model import Recipient, Sender

BLOCK_END = ".end"


class Context:
    """What a handler may use besides the service: the remaining input."""

    def __init__(self, lines):
        self.lines = lines

    def block(self):
        """Lines of a data block up to '.end'; raises if the input ends first."""
        out = []
        for line in self.lines:
            if line.raw.strip(lexer.BLANKS) == BLOCK_END:
                return out, True
            out.append(line)
        return out, False


# ---------------------------------------------------------------- setup

def cmd_sender(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 3, "sender NAME PLAN")
    name = lexer.name(toks[1], "sender")
    plan = toks[2]
    if plan not in billing.PLANS:
        raise CommandError("unknown plan " + plan)
    if name in svc.senders:
        raise CommandError("sender %s exists" % name)
    svc.senders[name] = Sender(name, plan, svc.now)
    svc.audit.add(svc.now, "sender", ("name", name), ("plan", plan))


def cmd_recipient(svc, line, ctx):
    toks = line.tokens
    lexer.need(toks, 2, "recipient NAME [tz=OFFSET]")
    name = lexer.name(toks[1], "recipient")
    opts, i = lexer.leading_options(toks, 2, ("tz",))
    if i != len(toks):
        raise CommandError("unexpected " + toks[i])
    offset = timefmt.parse_offset(opts["tz"]) if "tz" in opts else 0
    if name in svc.recipients:
        raise CommandError("recipient %s exists" % name)
    svc.recipients[name] = Recipient(name, offset, svc.now)
    svc.audit.add(svc.now, "recipient", ("name", name), ("tz", timefmt.fmt_offset(offset)))


def cmd_set(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 3, "set KEY VALUE")
    value = svc.cfg.parse_value(toks[1], toks[2])
    svc.cfg.set_global(toks[1], value)
    svc.audit.add(svc.now, "set", ("key", toks[1]), ("value", toks[2]))


def cmd_set_for(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 4, "set-for RECIPIENT KEY VALUE")
    svc.recipient(toks[1])
    value = svc.cfg.parse_value(toks[2], toks[3])
    svc.cfg.set_for(toks[1], toks[2], value)
    svc.audit.add(svc.now, "set-for", ("recipient", toks[1]), ("key", toks[2]),
                  ("value", toks[3]))


def cmd_unset_for(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 3, "unset-for RECIPIENT KEY")
    svc.recipient(toks[1])
    if toks[2] not in config.KEYS:
        raise CommandError("unknown key " + toks[2])
    svc.cfg.clear_for(toks[1], toks[2])
    svc.audit.add(svc.now, "unset-for", ("recipient", toks[1]), ("key", toks[2]))


def cmd_link(svc, line, ctx):
    toks = line.tokens
    usage = "link RECIPIENT ok | fail N | lost N | busy N SECONDS"
    lexer.need(toks, 3, usage)
    r = toks[1]
    svc.recipient(r)
    kind = toks[2]
    if kind == "ok":
        lexer.exact(toks, 3, usage)
        svc.links.clear(r)
        svc.audit.add(svc.now, "link", ("recipient", r), ("script", "clear"))
        return
    if kind in ("fail", "lost"):
        lexer.exact(toks, 4, usage)
        n = lexer.integer(toks[3], "count", 1, 1000)
        svc.links.script(r, link.FAIL if kind == "fail" else link.LOST, n)
        svc.audit.add(svc.now, "link", ("recipient", r), ("script", kind), ("count", n))
        return
    if kind == "busy":
        lexer.exact(toks, 5, usage)
        n = lexer.integer(toks[3], "count", 1, 1000)
        after = lexer.integer(toks[4], "seconds", 0, 86400)
        svc.links.script(r, link.BUSY, n, after)
        svc.audit.add(svc.now, "link", ("recipient", r), ("script", kind), ("count", n),
                      ("after", after))
        return
    raise CommandError("usage: " + usage)


# ---------------------------------------------------------------- messages

def cmd_send(svc, line, ctx):
    toks = line.tokens
    usage = "send ID SENDER RECIPIENT [prio=P] [ttl=DURATION] [after=DURATION] TEXT"
    lexer.need(toks, 5, usage)
    msg_id = lexer.msg_id(toks[1])
    opts, i = lexer.leading_options(toks, 4, intake.SEND_OPTIONS)
    text = line.rest(i)
    if not text:
        raise CommandError("usage: " + usage)
    parsed = intake.parse_options(opts)
    intake.submit(svc, intake.Request(msg_id, toks[2], toks[3], parsed, text, "send"))


def cmd_batch(svc, line, ctx):
    toks = line.tokens
    lexer.need(toks, 3, "batch SENDER RECIPIENT [prio=P] [ttl=DURATION] [after=DURATION]")
    block, closed = ctx.block()
    opts, i = lexer.leading_options(toks, 3, intake.SEND_OPTIONS)
    if i != len(toks):
        raise CommandError("unexpected " + toks[i])
    parsed = intake.parse_options(opts)
    svc.sender(toks[1])
    svc.recipient(toks[2])
    if not intake.has_room(svc, toks[2]):
        raise CommandError("recipient %s has no room" % toks[2])
    for n, item in enumerate(block, 1):
        if item.is_blank_or_comment():
            continue
        try:
            itoks = item.tokens
            if len(itoks) < 2:
                raise CommandError("usage: ID TEXT")
            msg_id = lexer.msg_id(itoks[0])
            req = intake.Request(msg_id, toks[1], toks[2], parsed, item.rest(1), "batch")
            intake.submit(svc, req, room_checked=True)
        except CommandError as exc:
            svc.emit("ERROR batch: line %d: %s" % (n, exc))
    if not closed:
        raise CommandError("missing " + BLOCK_END)


def cmd_cancel(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "cancel ID")
    msg = svc.message(toks[1])
    if not msg.pending:
        raise CommandError("message %s is %s" % (msg.id, msg.state))
    svc.dispatcher.cancel(msg, svc.now)
    svc.audit.add(svc.now, "cancel", ("id", msg.id))


# ---------------------------------------------------------------- clock

def cmd_advance(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "advance DURATION")
    svc.dispatcher.run_until(svc.now + timefmt.parse_duration(toks[1]))


def cmd_at(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 3, "at dN HH:MM[:SS[.mmm]]")
    target = timefmt.parse_instant(toks[1], toks[2])
    if target < svc.now:
        raise CommandError("%s is before now (%s)" % (
            timefmt.fmt_instant(target), timefmt.fmt_instant(svc.now)))
    svc.dispatcher.run_until(target)


def cmd_now(svc, line, ctx):
    lexer.exact(line.tokens, 1, "now")
    svc.emit("now " + timefmt.fmt_instant(svc.now))


# ---------------------------------------------------------------- listings

def cmd_queue(svc, line, ctx):
    lexer.exact(line.tokens, 1, "queue")
    for text in report.queue_lines(svc):
        svc.emit(text)


def cmd_show(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "show ID")
    for text in report.show_lines(svc.message(toks[1])):
        svc.emit(text)


def cmd_inbox(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "inbox RECIPIENT")
    for text in report.inbox_lines(svc.recipient(toks[1])):
        svc.emit(text)


def cmd_config(svc, line, ctx):
    toks = line.tokens
    if len(toks) > 2:
        raise CommandError("usage: config [RECIPIENT]")
    r = None
    if len(toks) == 2:
        r = svc.recipient(toks[1]).name
    for text in report.config_lines(svc, r):
        svc.emit(text)


def cmd_stats(svc, line, ctx):
    toks = line.tokens
    if len(toks) > 2:
        raise CommandError("usage: stats [RECIPIENT]")
    if len(toks) == 2:
        lines = stats.render_recipient(svc, svc.recipient(toks[1]).name)
    else:
        lines = stats.render(svc)
    for text in lines:
        svc.emit(text)


def cmd_snapshot(svc, line, ctx):
    lexer.exact(line.tokens, 1, "snapshot")
    for text in snapshot.lines(svc):
        svc.emit(text)


def cmd_invoice(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "invoice SENDER")
    sender = svc.sender(toks[1]).name
    number, lines = svc.billing.close(sender)
    if number is None:
        svc.emit("invoice %s: nothing to bill" % sender)
        return
    for text in report.invoice_lines(svc, sender, number, lines):
        svc.emit(text)
    svc.audit.add(svc.now, "invoice", ("sender", sender), ("number", number),
                  ("lines", len(lines)))


def cmd_plans(svc, line, ctx):
    lexer.exact(line.tokens, 1, "plans")
    for text in report.plan_lines(svc):
        svc.emit(text)


def cmd_history(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "history ID")
    msg = svc.message(toks[1])
    svc.emit("history %s: %d events" % (msg.id, len(msg.history)))
    for at, text in msg.history:
        svc.emit("%s %s" % (timefmt.fmt_instant(at), text))


def cmd_report(svc, line, ctx):
    toks = line.tokens
    usage = "report daily RECIPIENT | report senders | report retry"
    lexer.need(toks, 2, usage)
    if toks[1] == "daily":
        lexer.exact(toks, 3, usage)
        lines = report.daily_lines(svc, svc.recipient(toks[2]))
    elif toks[1] == "senders":
        lexer.exact(toks, 2, usage)
        lines = report.sender_lines(svc)
    elif toks[1] == "retry":
        lexer.exact(toks, 2, usage)
        lines = report.retry_lines(svc)
    else:
        raise CommandError("usage: " + usage)
    for text in lines:
        svc.emit(text)


def cmd_export(svc, line, ctx):
    toks = line.tokens
    usage = "export deliveries [RECIPIENT] | export billing [SENDER] | export audit"
    lexer.need(toks, 2, usage)
    kind = toks[1]
    if kind not in export.KINDS:
        raise CommandError("usage: " + usage)
    if kind == "audit":
        lexer.exact(toks, 2, usage)
        lines = export.audit_lines(svc)
    elif len(toks) == 3:
        who = svc.recipient(toks[2]).name if kind == "deliveries" else svc.sender(toks[2]).name
        lines = export.KINDS[kind](svc, who)
    else:
        lexer.exact(toks, 2, usage)
        lines = export.KINDS[kind](svc)
    for text in lines:
        svc.emit(text)


def cmd_explain(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "explain ID")
    for text in explain.lines(svc, svc.message(toks[1])):
        svc.emit(text)


def cmd_latency(svc, line, ctx):
    toks = line.tokens
    if len(toks) > 2:
        raise CommandError("usage: latency [RECIPIENT]")
    name = svc.recipient(toks[1]).name if len(toks) == 2 else None
    for text in latency.latency_lines(svc, name):
        svc.emit(text)


def cmd_timeline(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 2, "timeline ID")
    for text in latency.timeline_lines(svc.message(toks[1])):
        svc.emit(text)


def cmd_forecast(svc, line, ctx):
    toks = line.tokens
    lexer.exact(toks, 3, "forecast RECIPIENT SIZE")
    name = svc.recipient(toks[1]).name
    size = lexer.integer(toks[2], "size", 0, 1 << 20)
    for text in forecast.lines(svc, name, size):
        svc.emit(text)


def cmd_help(svc, line, ctx):
    toks = line.tokens
    if len(toks) > 2:
        raise CommandError("usage: help [COMMAND]")
    text = helptext.lines(toks[1] if len(toks) == 2 else None)
    if text is None:
        raise CommandError("no such command " + toks[1])
    for item in text:
        svc.emit(item)


def cmd_doctor(svc, line, ctx):
    lexer.exact(line.tokens, 1, "doctor")
    found = doctor.warnings(svc)
    svc.emit("doctor: %d warnings" % len(found))
    for text in found:
        svc.emit("warning " + text)


def cmd_audit(svc, line, ctx):
    toks = line.tokens
    if len(toks) > 2:
        raise CommandError("usage: audit [N]")
    last = lexer.integer(toks[1], "count") if len(toks) == 2 else None
    for text in svc.audit.lines(last):
        svc.emit(text)


COMMANDS = {
    "sender": cmd_sender,
    "recipient": cmd_recipient,
    "set": cmd_set,
    "set-for": cmd_set_for,
    "unset-for": cmd_unset_for,
    "link": cmd_link,
    "send": cmd_send,
    "batch": cmd_batch,
    "cancel": cmd_cancel,
    "advance": cmd_advance,
    "at": cmd_at,
    "now": cmd_now,
    "queue": cmd_queue,
    "show": cmd_show,
    "inbox": cmd_inbox,
    "config": cmd_config,
    "stats": cmd_stats,
    "invoice": cmd_invoice,
    "plans": cmd_plans,
    "audit": cmd_audit,
    "history": cmd_history,
    "report": cmd_report,
    "export": cmd_export,
    "doctor": cmd_doctor,
    "explain": cmd_explain,
    "latency": cmd_latency,
    "forecast": cmd_forecast,
    "timeline": cmd_timeline,
    "snapshot": cmd_snapshot,
    "help": cmd_help,
}


def run_line(svc, line, ctx):
    if line.is_blank_or_comment():
        return
    word = line.tokens[0]
    handler = COMMANDS.get(word)
    try:
        if handler is None:
            raise CommandError("unknown command")
        handler(svc, line, ctx)
    except CommandError as exc:
        svc.emit("ERROR %s: %s" % (word, exc))
    invariant.check_all(svc)
