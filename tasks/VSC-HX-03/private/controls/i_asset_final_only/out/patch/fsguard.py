# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Guarded filesystem access for one tenant.

Every file or folder that sitesmith opens, writes, lists or removes on behalf
of a tenant goes through a ``Guard``. The guard re-checks the real location
against the tenant root and stops the program with exit status 86 if it lies
outside. The modules above are required to have refused such a request long
before it gets here (see README, "Internal invariant"), so in a correct build
this check never fires.
"""

import os
import sys

import sitepath
from errors import SiteError

INVARIANT_EXIT = 86


def _violation(action):
    sys.stdout.flush()
    sys.stderr.write("INVARIANT: %s outside tenant root\n" % action)
    sys.stderr.flush()
    raise SystemExit(INVARIANT_EXIT)


class Guard:
    def __init__(self, root):
        self.root = os.path.realpath(root)

    def _checked(self, path, action):
        real = os.path.realpath(path)
        if not sitepath.inside(self.root, real):
            _violation(action)
        return real

    def _checked_parent(self, path, action):
        """For operations on a directory entry itself (not what it points to)."""
        parent = os.path.realpath(os.path.dirname(path))
        if not sitepath.inside(self.root, parent):
            _violation(action)
        return os.path.join(parent, os.path.basename(path))

    # -- reading ----------------------------------------------------------

    def read_bytes(self, path):
        real = self._checked(path, "read of file")
        try:
            with open(real, "rb") as handle:
                return handle.read()
        except FileNotFoundError:
            raise SiteError("not found") from None
        except IsADirectoryError:
            raise SiteError("not a file") from None

    def read_text(self, path):
        return self.read_bytes(path).decode("utf-8", "replace")

    def list_dir(self, path):
        """Sorted (name, kind) pairs; kind is 'dir', 'link' or 'file'."""
        real = self._checked(path, "listing of folder")
        found = []
        with os.scandir(real) as entries:
            for entry in entries:
                if entry.is_symlink():
                    kind = "link"
                elif entry.is_dir(follow_symlinks=False):
                    kind = "dir"
                else:
                    kind = "file"
                found.append((entry.name, kind))
        found.sort()
        return found

    # -- writing ----------------------------------------------------------

    def make_dirs(self, path):
        real = self._checked(path, "creation of folder")
        missing = []
        probe = real
        while not os.path.isdir(probe):
            missing.append(probe)
            probe = os.path.dirname(probe)
        for folder in reversed(missing):
            self._checked(folder, "creation of folder")
            try:
                os.mkdir(folder)
            except OSError:
                raise SiteError("cannot write") from None
        return real

    def write_bytes(self, path, data):
        real = self._checked(path, "write of file")
        self.make_dirs(os.path.dirname(real))
        try:
            with open(real, "wb") as handle:
                handle.write(data)
        except OSError:
            raise SiteError("cannot write") from None
        return real

    def remove_entry(self, path):
        """Remove a file or link (the link itself, never its target)."""
        entry = self._checked_parent(path, "removal of file")
        os.unlink(entry)

    def remove_empty_dir(self, path):
        entry = self._checked_parent(path, "removal of folder")
        os.rmdir(entry)
