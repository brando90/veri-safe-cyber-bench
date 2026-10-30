# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Registry accounts."""
import names
from errors import CommandError


class User:
    __slots__ = ("name", "admin", "disabled", "created_at")

    def __init__(self, name, admin, created_at):
        self.name = name
        self.admin = admin
        self.disabled = False
        self.created_at = created_at


class Users:
    def __init__(self, world):
        self.world = world
        self.by_name = {}

    def add(self, name, admin):
        if not names.valid_user(name):
            raise CommandError("bad_user", name)
        if name in self.by_name:
            raise CommandError("user_exists", name)
        user = User(name, admin, self.world.now)
        self.by_name[name] = user
        return user

    def get(self, name):
        user = self.by_name.get(name)
        if user is None:
            raise CommandError("unknown_user", name)
        return user

    def actor(self, name):
        user = self.get(name)
        if user.disabled:
            raise CommandError("disabled", name)
        return user

    def viewer(self, name):
        if name == "-":
            return None
        return self.actor(name)

    def remove(self, name):
        del self.by_name[name]

    def sorted(self):
        return [self.by_name[n] for n in sorted(self.by_name)]
