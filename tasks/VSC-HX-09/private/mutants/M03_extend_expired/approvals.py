# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Approvals: one-off exceptions to the policy.

An approval lets one subject perform actions matching an action pattern on
resources matching a resource pattern, once, within its validity window.

States and transitions:

    pending --grant--> approved --(used by a check)--> used
       |                  |
       +----revoke--------+-----> revoked
       +---(deadline)-----+-----> expired

`extend` moves the deadline of a pending or approved approval.  The state
is refreshed lazily: an approval whose deadline has passed is switched to
`expired` the next time anything looks at it.
"""
import clock
import limits
import numfmt
import patterns
from errors import ApprovalError

LIVE_STATES = ("pending", "approved")


class Approval:
    def __init__(self, aid, subject, action, resource, created, expires_at):
        self.id = aid
        self.subject = subject
        self.action = action
        self.resource = resource
        self.created = created
        self.expires_at = expires_at
        self.state = "pending"
        self.approver = None
        self.uses = []          # (time, deadline at that time)
        self.extensions = []    # (time, deadline before the extension)

    def label(self):
        return "A%d" % self.id


class ApprovalBook:
    def __init__(self):
        self.items = {}
        self.next_id = 1

    def ordered(self):
        return [self.items[k] for k in sorted(self.items)]


def parse_id(text):
    if not (text.startswith("A") and text[1:].isdigit() and text[1:2] != "0"):
        raise ApprovalError("bad approval id %s" % text)
    return int(text[1:])


def _get(sess, text):
    aid = parse_id(text)
    item = sess.approvals.items.get(aid)
    if item is None:
        raise ApprovalError("unknown approval %s" % text)
    return item


def _refresh(item, now):
    if item.state in LIVE_STATES and clock.expired(item.expires_at, now):
        item.state = "expired"


def _require_state(item, states):
    if item.state not in states:
        raise ApprovalError("%s is %s" % (item.label(), item.state))


def _require_live(item, now, states):
    _refresh(item, now)
    if item.state == "expired":
        raise ApprovalError("%s has expired" % item.label())
    _require_state(item, states)


def request(sess, subject, action, resource, ttl):
    patterns.check_action(action)
    patterns.check_resource(resource)
    if ttl > limits.MAX_TTL:
        raise ApprovalError("ttl longer than %s" % numfmt.fmt_duration(limits.MAX_TTL))
    book = sess.approvals
    now = sess.clock.now
    item = Approval(book.next_id, subject, action, resource, now, now + ttl)
    book.items[item.id] = item
    book.next_id += 1
    return item


def grant(sess, text, approver):
    item = _get(sess, text)
    _require_live(item, sess.clock.now, ("pending",))
    if approver == item.subject:
        raise ApprovalError("%s cannot approve their own request" % approver)
    item.state = "approved"
    item.approver = approver
    return item


def revoke(sess, text):
    item = _get(sess, text)
    _refresh(item, sess.clock.now)
    _require_state(item, ("pending", "approved", "expired"))
    item.state = "revoked"
    return item


def extend(sess, text, seconds):
    item = _get(sess, text)
    now = sess.clock.now
    _require_state(item, LIVE_STATES)
    new_deadline = item.expires_at + seconds
    if new_deadline - item.created > limits.MAX_TTL:
        raise ApprovalError("%s would last longer than %s" % (
            item.label(), numfmt.fmt_duration(limits.MAX_TTL)))
    item.extensions.append((now, item.expires_at))
    item.expires_at = new_deadline
    return item


def _covers(item, action, resource):
    return (patterns.match_action(item.action, action)
            and patterns.match_resource(item.resource, resource))


def find_usable(sess, subject, action, resource):
    """The oldest approved, unexpired approval for this request, or None."""
    now = sess.clock.now
    for item in sess.approvals.ordered():
        _refresh(item, now)
        if item.state != "approved" or item.subject != subject:
            continue
        if _covers(item, action, resource):
            return item
    return None


def consume(sess, item):
    """Record the use of an approval found by find_usable()."""
    item.uses.append((sess.clock.now, item.expires_at))
    item.state = "used"


def listing(sess):
    now = sess.clock.now
    lines = []
    for item in sess.approvals.ordered():
        _refresh(item, now)
        line = "%s %s %s %s %s" % (item.label(), item.state, item.subject, item.action,
                                   item.resource)
        if item.state in LIVE_STATES:
            line += " left=%s" % numfmt.fmt_duration(clock.remaining(item.expires_at, now))
        if item.approver:
            line += " by=%s" % item.approver
        lines.append(line)
    return lines
