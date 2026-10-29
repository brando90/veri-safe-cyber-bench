# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""User and role commands."""

import parse
import roles
import store
from errors import CommandError

def cmd_as(sess, line):
    toks = parse.tokens(line)
    user = toks[1] if len(toks) > 1 else "nobody"
    sess.actor = user
    sess.out.write("OK actor %s\n" % user)

def cmd_whoami(sess, line):
    actor = sess.actor
    role = sess.role
    sess.out.write("actor %s role %s\n" % (actor, role if role else "none"))

def cmd_perms(sess, line):
    toks = parse.tokens(line)
    role = toks[1] if len(toks) > 1 else sess.role
    perms = roles.effective(sess.conn, role)
    sess.out.write("%s: %s\n" % (role, ' '.join(sorted(perms)) if perms else '(none)'))

def cmd_user_add(sess, line):
    toks = parse.tokens(line)
    user, role = toks[1], toks[2]
    store.user_add(sess.conn, user, role)
    sess.out.write("OK user %s role %s\n" % (user, role))

def cmd_role_add(sess, line):
    toks = parse.tokens(line)
    role, *parents = toks[1:]
    parents = [p.rstrip(',') for p in parents]
    store.role_add(sess.conn, role, parents)
    sess.out.write("OK role %s\n" % role)

def cmd_role_grant(sess, line):
    toks = parse.tokens(line)
    role, perm = toks[1], toks[2]
    store.role_rule(sess.conn, role, 'grant', perm)
    roles.invalidate(role)
    sess.out.write("OK role %s grant %s\n" % (role, perm))

def cmd_role_deny(sess, line):
    toks = parse.tokens(line)
    role, perm = toks[1], toks[2]
    store.role_rule(sess.conn, role, 'deny', perm)
    roles.invalidate(role)
    sess.out.write("OK role %s deny %s\n" % (role, perm))