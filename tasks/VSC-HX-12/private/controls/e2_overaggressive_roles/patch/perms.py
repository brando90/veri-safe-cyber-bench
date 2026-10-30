# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Package roles and what each role may do."""
from errors import CommandError

ROLES = ("owner", "maintainer", "reader")
LEVEL = {"reader": 1, "maintainer": 2, "owner": 3}

ACTION_ROLE = {
    "read": "reader",
    "fetch": "reader",
    "publish": "maintainer",
    "tag": "maintainer",
    "deprecate": "maintainer",
    "yank": "maintainer",
    "unyank": "maintainer",
    "unpublish": "owner",
    "owner": "owner",
    "visibility": "owner",
}

# Actions anyone (even without a user name) may take on a public package.
PUBLIC_ACTIONS = frozenset({"read", "fetch"})

# Actions a site administrator may take on any package without a role.
ADMIN_ACTIONS = frozenset({"yank", "unyank", "unpublish"})

VERB = {
    "read": "read",
    "fetch": "fetch from",
    "publish": "publish to",
    "tag": "change tags of",
    "deprecate": "deprecate releases of",
    "yank": "yank releases of",
    "unyank": "unyank releases of",
    "unpublish": "unpublish releases of",
    "owner": "manage roles of",
    "visibility": "change visibility of",
}


def role_of(pkg, user):
    if user is None:
        return None
    return pkg.roles.get(user.name)


def can(w, user, pkg, action):
    if action in PUBLIC_ACTIONS and pkg.visibility == "public":
        return True
    if user is None:
        return False
    if user.admin and action in ADMIN_ACTIONS:
        return True
    role = pkg.roles.get(user.name)
    return role is not None and LEVEL[role] >= LEVEL[ACTION_ROLE[action]]


def require(w, user, pkg, action):
    if can(w, user, pkg, action):
        return
    if action == "read" or not can(w, user, pkg, "read"):
        raise CommandError("unknown_package", pkg.name)
    raise CommandError("denied", user.name if user else "-", VERB[action], pkg.name)


def require_admin(user):
    if not user.admin:
        raise CommandError("admin_only", user.name)


def owner_count(pkg):
    return sum(1 for r in pkg.roles.values() if r == "owner")
