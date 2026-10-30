# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Text of the ``help`` command (one usage line per command, grouped)."""

GROUPS = (
    ("setup", (
        ("sender NAME PLAN", "register a sender; PLAN is basic, bulk or pro"),
        ("recipient NAME [tz=OFFSET]", "register a recipient with a fixed UTC offset"),
        ("set KEY VALUE", "global configuration override"),
        ("set-for RECIPIENT KEY VALUE", "per-recipient override (recipient keys)"),
        ("unset-for RECIPIENT KEY", "remove a per-recipient override"),
        ("link RECIPIENT ok|fail N|lost N|busy N SECONDS", "script link outcomes"),
    )),
    ("messages", (
        ("send ID SENDER RECIPIENT [prio=P] [ttl=D] [after=D] TEXT", "submit one message"),
        ("batch SENDER RECIPIENT [prio=P] [ttl=D] [after=D]", "submit ID TEXT lines up to .end"),
        ("cancel ID", "cancel a pending message"),
    )),
    ("clock", (
        ("advance DURATION", "move the clock forward, running dispatch rounds"),
        ("at dN HH:MM[:SS[.mmm]]", "move the clock to an instant"),
        ("now", "print the clock"),
    )),
    ("listings", (
        ("queue", "fragments waiting, in dispatch order"),
        ("show ID", "one message and its fragments"),
        ("history ID", "events of one message"),
        ("explain ID", "why a pending message is not being attempted"),
        ("inbox RECIPIENT", "delivered messages of a recipient"),
        ("config [RECIPIENT]", "effective configuration"),
        ("stats [RECIPIENT]", "counters and per-recipient figures"),
        ("snapshot", "deterministic dump of the whole state"),
        ("latency [RECIPIENT]", "delivery-time percentiles and histogram"),
        ("timeline ID", "events of one message with time since acceptance"),
        ("forecast RECIPIENT SIZE", "earliest instant the limits let a message start"),
        ("invoice SENDER", "bill the open lines of a sender"),
        ("plans", "revenue per plan"),
        ("report daily RECIPIENT|senders|retry", "other reports"),
        ("export deliveries|billing|audit [NAME]", "CSV exports"),
        ("audit [N]", "audit log"),
        ("doctor", "configuration warnings"),
        ("help [COMMAND]", "this text"),
    )),
)


def usage_of(command):
    for _, items in GROUPS:
        for usage, text in items:
            if usage.split(" ", 1)[0] == command:
                return usage, text
    return None


def lines(command=None):
    if command is not None:
        found = usage_of(command)
        if found is None:
            return None
        return ["%s  -  %s" % found]
    out = []
    for title, items in GROUPS:
        out.append("%s:" % title)
        for usage, text in items:
            out.append("  %s  -  %s" % (usage, text))
    return out
