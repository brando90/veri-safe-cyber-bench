# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Applies a policy to a stored record to produce its exported form."""
import copy

import maskers
import scanner
import stamp


def apply(record, policy):
    """Return (view, changed): the exported form of RECORD and the changed names."""
    view = copy.copy(record)
    view.fields = dict(record.fields)
    changed = []
    for name in sorted(view.fields):
        action = policy.action_for(name)
        if action is None:
            continue
        value = view.fields[name]
        if action == "drop":
            del view.fields[name]
        elif action == "redact":
            view.fields[name] = maskers.REDACTED
        elif action == "pseudo":
            view.fields[name] = maskers.pseudo(value, policy.salt)
        else:
            view.fields[name] = maskers.partial(value)
        changed.append(name)
    view.message = scanner.scrub(view.message)
    return view, changed


MAX_MESSAGE = 80
CUT = 77


def shorten(text):
    """Messages longer than MAX_MESSAGE characters are cut to CUT plus '...'."""
    if len(text) > MAX_MESSAGE:
        return text[:CUT] + "..."
    return text


def line(view):
    parts = ["#%d" % view.id, stamp.fmt(view.when), view.source, view.user]
    parts.extend("%s=%s" % (n, view.fields[n]) for n in sorted(view.fields))
    text = " ".join(parts)
    if view.message:
        text += " -- " + shorten(view.message)
    return text


def old_line(view):
    return "%s|%s|%s" % (stamp.fmt(view.when), view.source, view.message)
