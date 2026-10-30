# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""`whatif SET_A SET_B`: compare two sets on a block of requests.

The block (up to `.end`) holds one request per line:

    SUBJECT ACTION RESOURCE [KEY=VALUE ...]

Each request is decided against both sets without using approvals and
without logging.  Output, one line per request, then a summary:

    SAME n allow by=R1|R1
    DIFF n allow>deny by=R1|R4
    -- 3 requests, 1 different (33.3%)

A request line that is not valid prints `BAD n <reason>` and counts as
neither same nor different.
"""
import decide
import numfmt
import redact
from errors import PFError, UsageError

MAX_REQUESTS = 200


def _parse(line):
    toks = line.split()
    if len(toks) < 3:
        raise UsageError("expected SUBJECT ACTION RESOURCE")
    attrs = {}
    for tok in toks[3:]:
        key, sep, value = tok.partition("=")
        if not sep or not key or not value or key in attrs:
            raise UsageError("bad attribute %s" % tok)
        attrs[key] = value
    return toks[0], toks[1], toks[2], attrs


def compare(sess, set_a, set_b, block):
    sess.store.get(set_a)
    sess.store.get(set_b)
    requests = [line.strip() for line in block if line.strip()]
    if len(requests) > MAX_REQUESTS:
        raise UsageError("more than %d requests" % MAX_REQUESTS)
    lines = []
    same = differ = 0
    for n, line in enumerate(requests, start=1):
        try:
            subject, action, resource, attrs = _parse(line)
            a = decide.decide(sess, set_a, subject, action, resource, attrs,
                              use_approvals=False)
            b = decide.decide(sess, set_b, subject, action, resource, attrs,
                              use_approvals=False)
        except PFError as exc:
            lines.append(redact.scrub(sess, "BAD %d %s" % (n, exc.message)))
            continue
        if a.effect == b.effect:
            same += 1
            lines.append("SAME %d %s by=%s|%s" % (n, a.effect, a.by, b.by))
        else:
            differ += 1
            lines.append("DIFF %d %s>%s by=%s|%s" % (n, a.effect, b.effect, a.by, b.by))
    counted = same + differ
    pct = numfmt.pct1(differ, counted) + "%" if counted else "-"
    lines.append("-- %s, %d different (%s)" % (numfmt.plural(counted, "request"), differ, pct))
    return lines
