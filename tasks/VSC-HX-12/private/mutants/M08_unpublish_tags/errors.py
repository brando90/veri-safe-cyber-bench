# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exit codes, the error message table and the two exception types."""

EXIT_OK = 0
EXIT_INVARIANT = 86

MESSAGES = {
    "usage": "usage: %s",
    "unknown_command": "unknown command '%s'",
    "bad_quoting": "unbalanced double quote",
    "dup_option": "option %s given twice",
    "bad_option": "unknown option '%s' for %s",
    "clock_back": "the clock cannot go back (now %d)",
    "unknown_user": "unknown user %s",
    "user_exists": "user %s already exists",
    "bad_user": "invalid user name '%s'",
    "disabled": "user %s is disabled",
    "not_disabled": "user %s is not disabled",
    "admin_only": "%s is not an administrator",
    "bad_name": "invalid package name '%s'",
    "reserved": "package name %s is reserved",
    "unknown_package": "unknown package %s",
    "bad_version": "invalid version '%s'",
    "unknown_version": "%s has no version %s",
    "version_exists": "%s %s already exists",
    "version_burned": "%s %s was unpublished and cannot be reused",
    "bad_req": "bad requirement '%s'",
    "bad_deps": "bad dependency list '%s'",
    "self_dep": "%s cannot depend on itself",
    "bad_size": "invalid size '%s'",
    "bad_duration": "invalid duration '%s'",
    "bad_number": "invalid number '%s'",
    "bad_visibility": "invalid visibility '%s'",
    "denied": "%s may not %s %s",
    "quota_exceeded": "quota exceeded for %s: %d KiB used, %d KiB more, limit %d KiB",
    "no_match": "no version of %s matches %s",
    "no_latest": "%s has no latest version",
    "unknown_tag": "%s has no tag %s",
    "managed_tag": "tag %s is managed by the registry",
    "bad_tag": "invalid tag name '%s'",
    "embargoed": "%s %s is under embargo until %d",
    "grace_over": "%s %s can no longer be unpublished (published at %d)",
    "already_yanked": "%s %s is already yanked",
    "not_yanked": "%s %s is not yanked",
    "last_owner": "cannot remove the last owner of %s",
    "no_invite": "no pending invite for %s to %s",
    "invite_expired": "invite for %s to %s expired",
    "already_member": "%s already has role %s on %s",
    "not_member": "%s has no role on %s",
    "bad_role": "invalid role '%s'",
    "ttl_too_long": "invite ttl %s is longer than %s",
    "conflict": "cannot satisfy requirements for %s: %s",
    "too_deep": "dependency resolution did not settle for %s",
    "bad_root": "invalid lock root '%s'",
    "unknown_lock": "no lock named %s",
    "bad_report": "unknown report '%s'",
    "bad_format": "unknown export format '%s'",
}


class CommandError(Exception):
    """A refused or malformed command.  Printed as ``error: MESSAGE``."""

    def __init__(self, code, *args):
        self.code = code
        self.params = args
        super().__init__(MESSAGES[code] % args)


class InvariantViolation(Exception):
    """The consistency check found a broken rule."""
