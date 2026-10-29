# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Actor switching, users and roles."""

import audit
import parse
import roles
import store
from errors import CommandError


def _exact(line, n, usage_text):
    toks, rest = parse.take(line, n)
    if rest is None or rest != "":
        raise parse.usage(usage_text)
    return toks


def _role(sess, name):
    row = store.role_row(sess.conn, name)
    if row is None:
        raise CommandError("unknown-role: " + name)
    return row


def cmd_as(sess, line):
    name = _exact(line, 2, "as USER")[1]
    if name == "nobody":
        sess.actor = None
    elif store.user_role(sess.conn, name) is None:
        raise CommandError("unknown-user: " + name)
    else:
        sess.actor = name
    sess.emit("OK actor " + name)


def cmd_whoami(sess, line):
    _exact(line, 1, "whoami")
    sess.emit("actor %s role %s" % (sess.actor_name(), sess.role() or "none"))


def cmd_perms(sess, line):
    name = _exact(line, 2, "perms ROLE")[1]
    _role(sess, name)
    held = sorted(roles.effective(sess.conn, name))
    sess.emit("%s: %s" % (name, " ".join(held) if held else "(none)"))


def cmd_user_add(sess, line):
    toks = _exact(line, 3, "user-add USER ROLE")
    name = parse.user_name(toks[1])
    if store.user_role(sess.conn, name) is not None:
        raise CommandError("duplicate-user: " + name)
    role = toks[2]
    _role(sess, role)
    store.add_user(sess.conn, name, role)
    sess.expect.add("users")
    audit.record(sess, "user.add", name, [("role", role)])
    sess.emit("OK user %s role %s" % (name, role))


def cmd_role_add(sess, line):
    usage_text = "role-add ROLE PARENT[,PARENT...]"
    toks = _exact(line, 3, usage_text)
    name = parse.role_name(toks[1])
    if store.role_row(sess.conn, name) is not None:
        raise CommandError("duplicate-role: " + name)
    parents = toks[2].split(",")
    if "" in parents or len(set(parents)) != len(parents):
        raise parse.usage(usage_text)
    for parent in parents:
        _role(sess, parent)
    store.add_role(sess.conn, name, parents)
    sess.expect.add("roles")
    sess.expect.add("role_parents", len(parents))
    roles.invalidate(name)
    audit.record(sess, "role.add", name, [("parents", ",".join(parents))])
    sess.emit("OK role " + name)


def _rule(sess, line, effect):
    toks = _exact(line, 3, "role-%s ROLE PERM" % effect)
    name, perm = toks[1], toks[2]
    row = _role(sess, name)
    if row["builtin"]:
        raise CommandError("builtin-role: " + name)
    if perm not in roles.PERMS:
        raise CommandError("unknown-perm: " + perm)
    if (perm, effect) in store.role_rules(sess.conn, name):
        raise CommandError("duplicate-rule: %s %s %s" % (name, effect, perm))
    store.add_rule(sess.conn, name, perm, effect)
    sess.expect.add("role_rules")
    roles.invalidate(name)
    audit.record(sess, "role." + effect, name, [("perm", perm)])
    sess.emit("OK role %s %s %s" % (name, effect, perm))


def cmd_role_grant(sess, line):
    _rule(sess, line, "grant")


def cmd_role_deny(sess, line):
    _rule(sess, line, "deny")
