# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The World: every component wired together, plus the command table."""
import accounts
import audit
import clock
import export
import fetch
import helptext
import info
import invariant
import lifecycle
import lockfile
import owners
import publish
import quota
import registry
import resolver
import stats
import tags
import users
from errors import CommandError

# name: (handler, usage, options, min args, max args or None)
COMMANDS = {
    "clock set": (clock.cmd_set, "clock set T", (), 1, 1),
    "clock advance": (clock.cmd_advance, "clock advance DURATION", (), 1, 1),
    "clock show": (clock.cmd_show, "clock show", (), 0, 0),
    "user add": (accounts.cmd_add, "user add NAME [admin]", (), 1, 2),
    "user disable": (accounts.cmd_disable, "user disable ACTOR NAME", (), 2, 2),
    "user enable": (accounts.cmd_enable, "user enable ACTOR NAME", (), 2, 2),
    "user remove": (accounts.cmd_remove, "user remove ACTOR NAME", (), 2, 2),
    "user show": (accounts.cmd_show, "user show NAME", (), 1, 1),
    "publish": (publish.cmd_publish,
                "publish ACTOR PACKAGE VERSION [size=SIZE] [deps=LIST] [embargo=DURATION] "
                "[visibility=public|private]",
                ("size", "deps", "embargo", "visibility"), 3, 3),
    "yank": (lifecycle.cmd_yank, "yank ACTOR PACKAGE VERSION [reason=TEXT]", ("reason",), 3, 3),
    "unyank": (lifecycle.cmd_unyank, "unyank ACTOR PACKAGE VERSION", (), 3, 3),
    "deprecate": (lifecycle.cmd_deprecate, "deprecate ACTOR PACKAGE VERSION [message=TEXT]",
                  ("message",), 3, 3),
    "unpublish": (lifecycle.cmd_unpublish, "unpublish ACTOR PACKAGE VERSION", (), 3, 3),
    "prune": (lifecycle.cmd_prune, "prune ACTOR PACKAGE", (), 2, 2),
    "package delete": (lifecycle.cmd_delete, "package delete ACTOR PACKAGE", (), 2, 2),
    "visibility": (lifecycle.cmd_visibility, "visibility ACTOR PACKAGE public|private", (), 3, 3),
    "tag add": (tags.cmd_add, "tag add ACTOR PACKAGE TAG VERSION", (), 4, 4),
    "tag rm": (tags.cmd_rm, "tag rm ACTOR PACKAGE TAG", (), 3, 3),
    "tags": (tags.cmd_list, "tags VIEWER PACKAGE", (), 2, 2),
    "owner invite": (owners.cmd_invite, "owner invite ACTOR PACKAGE USER [role=ROLE] [ttl=DURATION]",
                     ("role", "ttl"), 3, 3),
    "owner accept": (owners.cmd_accept, "owner accept ACTOR PACKAGE", (), 2, 2),
    "owner remove": (owners.cmd_remove, "owner remove ACTOR PACKAGE USER", (), 3, 3),
    "roles": (owners.cmd_roles, "roles VIEWER PACKAGE", (), 2, 2),
    "invites": (owners.cmd_invites, "invites ACTOR PACKAGE", (), 2, 2),
    "resolve": (resolver.cmd_resolve, "resolve VIEWER PACKAGE REQUIREMENT", (), 3, 3),
    "fetch": (fetch.cmd_fetch, "fetch VIEWER PACKAGE [REQUIREMENT|@TAG]", (), 2, 3),
    "lock": (lockfile.cmd_lock, "lock VIEWER NAME PACKAGE@REQUIREMENT...", (), 3, None),
    "outdated": (lockfile.cmd_outdated, "outdated VIEWER LOCKNAME", (), 2, 2),
    "info": (info.cmd_info, "info VIEWER PACKAGE", (), 2, 2),
    "dependents": (info.cmd_dependents, "dependents VIEWER PACKAGE", (), 2, 2),
    "search": (stats.cmd_search, "search VIEWER TEXT", (), 2, 2),
    "top": (stats.cmd_top, "top VIEWER downloads|releases|dependents|size [n=N]", ("n",), 2, 2),
    "quota": (quota.cmd_show, "quota USER", (), 1, 1),
    "quota set": (quota.cmd_set, "quota set ACTOR USER KIB", (), 3, 3),
    "audit": (audit.cmd_audit, "audit [n=N]", ("n",), 0, 0),
    "export audit": (export.cmd_export, "export audit tsv|csv", (), 1, 1),
    "check": (invariant.cmd_check, "check", (), 0, 0),
    "help": (helptext.cmd_help, "help [COMMAND]", (), 0, 2),
}


class World:
    def __init__(self, out):
        self.out = out
        self.clock = clock.Clock()
        self.users = users.Users(self)
        self.registry = registry.Registry(self)
        self.quota = quota.Quota(self)
        self.audit = audit.AuditLog(self)
        self.locks = {}

    @property
    def now(self):
        return self.clock.now

    def emit(self, line):
        self.out.emit(line)

    def dispatch(self, cmd):
        words = cmd.words
        if len(words) >= 2 and "%s %s" % (words[0], words[1]) in COMMANDS:
            name, args = "%s %s" % (words[0], words[1]), words[2:]
        elif words[0] in COMMANDS:
            name, args = words[0], words[1:]
        else:
            raise CommandError("unknown_command", words[0])
        handler, usage, options, lo, hi = COMMANDS[name]
        for opt in sorted(cmd.opts):
            if opt not in options:
                raise CommandError("bad_option", opt, name)
        cmd.name, cmd.args, cmd.usage = name, args, usage
        if len(args) < lo or (hi is not None and len(args) > hi):
            raise CommandError("usage", usage)
        handler(self, cmd)
