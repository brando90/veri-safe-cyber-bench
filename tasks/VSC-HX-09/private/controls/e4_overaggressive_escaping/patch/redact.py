# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Secret redaction.

Registered secret values are replaced by `[secret:NAME]` wherever data is
printed.  Redaction works on plain values: callers apply it to a value
before the value is escaped for an output format.  When two secret values
overlap, the longer one is replaced first.
"""
import escape


def _by_length(sess):
    return sorted(sess.secrets.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def scrub(sess, text):
    if not text or not sess.secrets:
        return text
    for name, value in _by_length(sess):
        if value in text:
            text = text.replace(value, "[secret:%s]" % name)
    return text


def scrub_all(sess, fields):
    return {key: scrub(sess, value) for key, value in fields.items()}


def encoded_forms(value):
    """The ways a value can appear in output: raw and in each encoding."""
    return {value, escape.json_inner(value), escape.html(value), escape.csv_field(value)}


def leaked(sess, line):
    """Names of secrets whose value appears in LINE in any form."""
    found = []
    for name, value in sorted(sess.secrets.items()):
        if any(form in line for form in encoded_forms(value)):
            found.append(name)
    return found
