# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Registry-wide policy tables."""

HOUR = 3600
DAY = 24 * HOUR

# How long after publishing a release it may still be unpublished, by release
# kind.  None: no limit.
UNPUBLISH_GRACE = {
    "stable": 72 * HOUR,
    "prerelease": None,
}

# Package roles that may fetch and resolve a release while it is embargoed.
EMBARGO_BYPASS_ROLES = frozenset()

# Requirement kinds that may select a yanked release.
YANKED_SELECTABLE = frozenset({"exact"})

# Invite lifetime: default and upper bound per offered role.
INVITE_TTL_DEFAULT = DAY
INVITE_TTL_MAX = {
    "owner": 2 * DAY,
    "maintainer": 7 * DAY,
    "reader": 30 * DAY,
}

QUOTA_DEFAULT_KIB = 10240

TOP_DEFAULT = 5
TOP_MAX = 50

AUDIT_DEFAULT = 20
