# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Roles, inheritance and permission resolution.

See README, "Roles and permissions".  Built-in roles are created when the
database is opened and cannot be changed; custom roles are added with
role-add and changed with role-grant / role-deny.

Resolved permission sets are cached per role name because every command
asks for them at least twice (dispatcher and consistency check).
"""

import store

PERMS = (
    "appt.cancel", "appt.view", "appt.write", "audit.view", "customer.view",
    "customer.write", "export.run", "import.run", "invoice.view", "invoice.void",
    "invoice.write", "payment.record", "report.view", "role.manage",
    "service.write", "user.manage",
)

# name, parents, grants, denies
BUILTIN = (
    ("viewer", (), ("customer.view", "appt.view", "invoice.view", "report.view"), ()),
    ("frontdesk", ("viewer",), ("customer.write", "appt.write"), ()),
    ("trainee", ("frontdesk",), (), ("customer.write",)),
    ("billing", ("viewer",), ("invoice.write", "payment.record", "export.run",
                              "import.run"), ()),
    ("manager", ("frontdesk", "billing"), ("appt.cancel", "invoice.void", "service.write",
                                           "audit.view"), ()),
    ("owner", ("manager",), ("user.manage", "role.manage"), ()),
)

FIRST_USER = ("owner", "owner")

_cache = {}


def reset():
    _cache.clear()


def ancestors(conn, role):
    """ROLE followed by all of its ancestors, each once, nearest first."""
    seen = [role]
    i = 0
    while i < len(seen):
        for parent in store.role_parents(conn, seen[i]):
            if parent not in seen:
                seen.append(parent)
        i += 1
    return seen


def effective(conn, role, fresh=False):
    """The frozenset of permissions ROLE holds (empty for None/unknown)."""
    if role is None:
        return frozenset()
    if not fresh and role in _cache:
        return _cache[role]
    if store.role_row(conn, role) is None:
        return frozenset()
    grants, denies = set(), set()
    for name in ancestors(conn, role):
        for perm, effect in store.role_rules(conn, name):
            if effect == "grant":
                grants.add(perm)
            else:
                denies.add(perm)
    result = frozenset(grants - denies)
    if not fresh:
        _cache[role] = result
    return result


def can(conn, role, perm):
    return perm in effective(conn, role)


def invalidate(role):
    """Forget cached sets after ROLE changed (its descendants change too)."""
    _cache.clear()
