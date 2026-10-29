# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Built-in plugins and the hook registry.

A tenant enables plugins in site.cfg (``plugin NAME ARG...``). Plugins are not
code: each name below is a small built-in behaviour attached to one hook.

    banner FILE        pre_render   prepend the text of src/FILE to every page
    footer TEXT...     post_render  append one line of text to every page
    rename FROM TO     output_path  output paths under FROM (relative to out/)
                                    are moved under TO
    copy SRC DEST      post_build   copy the files below src/SRC to out/DEST

Plugin arguments are site path text. They are interpreted each time they are
used, never when site.cfg is read.
"""

import os

import sitepath
from errors import SiteError

HOOKS = ("pre_render", "post_render", "output_path", "post_build")

# name -> (hook, minimum args, maximum args or None)
KNOWN = {
    "banner": ("pre_render", 1, 1),
    "footer": ("post_render", 1, None),
    "rename": ("output_path", 2, 2),
    "copy": ("post_build", 2, 2),
}


class Plugin:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.hook = KNOWN[name][0]

    def describe(self):
        return " ".join([self.hook, self.name] + self.args)


class HookRegistry:
    def __init__(self, specs):
        self._by_hook = {hook: [] for hook in HOOKS}
        self._order = []
        for name, args in specs:
            if name not in KNOWN:
                raise SiteError("unknown plugin " + name)
            _, low, high = KNOWN[name]
            if len(args) < low or (high is not None and len(args) > high):
                raise SiteError("bad plugin arguments for " + name)
            plugin = Plugin(name, list(args))
            self._by_hook[plugin.hook].append(plugin)
            self._order.append(plugin)

    def describe(self):
        return [plugin.describe() for plugin in self._order]

    # -- pre_render / post_render ------------------------------------------

    def pre_render(self, tenant, text, deps):
        """Apply banner plugins; every file read is recorded in ``deps``."""
        for plugin in self._by_hook["pre_render"]:
            real = tenant.locate(tenant.src, plugin.args[0])
            banner = tenant.read_text(real)
            deps.record(real, banner)
            if banner and not banner.endswith("\n"):
                banner += "\n"
            text = banner + text
        return text

    def post_render(self, text):
        for plugin in self._by_hook["post_render"]:
            if text and not text.endswith("\n"):
                text += "\n"
            text += " ".join(plugin.args) + "\n"
        return text

    # -- output_path ---------------------------------------------------------

    def output_path(self, rel):
        """Map an output path (site path text relative to out/) through rename plugins.

        The result is again site path text relative to out/; the caller decides
        whether it is acceptable.
        """
        parts = sitepath.normalise(rel)
        for plugin in self._by_hook["output_path"]:
            prefix = sitepath.normalise(plugin.args[0])
            if prefix and sitepath.starts_with(parts, prefix):
                rest = parts[len(prefix):]
                rel = "/".join([plugin.args[1]] + rest)
                parts = sitepath.normalise(rel)
        return rel

    # -- post_build ----------------------------------------------------------

    def copy_plan(self, tenant):
        """List of (source location, destination location, display) for copy plugins.

        Every source file and every destination is checked here; nothing is
        written by this method.
        """
        plan = []
        for plugin in self._by_hook["post_build"]:
            src_dir = tenant.locate(tenant.src, plugin.args[0])
            if not os.path.isdir(src_dir):
                raise SiteError("copy source is not a folder")
            files = tenant.walk_files(src_dir)
            dest_dir_text = plugin.args[1]
            entries = []
            for real, rel in files:
                dest = tenant.locate_for_write(tenant.out, tenant.out,
                                               dest_dir_text + "/" + rel)
                entries.append((real, dest))
            shown = sitepath.display(tenant.root,
                                     sitepath.join(tenant.out, dest_dir_text))
            plan.append((entries, shown))
        return plan

