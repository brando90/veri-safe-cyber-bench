#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Derive the public (defective) source tree and the K mutants from gold.

Each variant is a list of exact text replacements (file, gold text, defective
text). public/src = gold with every variant applied; mutants/<id>/ = gold with
exactly one variant applied. Run from anywhere: python3 make_variants.py
"""

import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
GOLD = os.path.join(HERE, "gold")
PUBLIC = os.path.join(os.path.dirname(HERE), "public", "src")
MUTANTS = os.path.join(HERE, "mutants")

VARIANTS = [
    ("m1_dynamic_include", [
        ("template.py",
         "            name = substitute(node.name, variables)\n"
         "            real = self.tenant.locate(self.tenant.src, name)\n",
         "            name = substitute(node.name, variables)\n"
         "            real = sitepath.join(self.tenant.src, name)\n"),
    ]),
    ("m2_bundle_import_text_check", [
        ("bundler.py",
         "from errors import SiteError\n",
         "from errors import OUTSIDE_TENANT, Denied, SiteError\n"),
        ("bundler.py",
         "            here = os.path.dirname(real)\n"
         "            self._add(self.tenant.locate(here, target), depth + 1)\n",
         "            joined = os.path.normpath(os.path.join(os.path.dirname(real), target))\n"
         "            if not joined.startswith(self.tenant.root):\n"
         "                raise Denied(OUTSIDE_TENANT)\n"
         "            self._add(os.path.realpath(joined), depth + 1)\n"),
    ]),
    ("m3_cache_key_without_tenant", [
        ("cache.py",
         "    for part in (tenant.root, page_rel, source, tenant.config.fingerprint(), session):\n",
         "    for part in (page_rel, source, tenant.config.fingerprint(), session):\n"),
    ]),
    ("m4_import_member_raw_check", [
        ("archive.py",
         "from errors import SiteError\n",
         "from errors import OUTSIDE_AREA, Denied, SiteError\n"),
        ("archive.py",
         "        dest = tenant.locate_for_write(theme_dir, theme_dir, member)\n"
         "        plan.append((dest, content))\n",
         "        if \"..\" in member.split(\"/\"):\n"
         "            raise Denied(OUTSIDE_AREA)\n"
         "        plan.append((sitepath.join(theme_dir, member), content))\n"),
    ]),
    ("m5_output_path_hook_unchecked", [
        ("builder.py",
         "        target = tenant.hooks.output_path(rel)\n"
         "        dest = tenant.locate_for_write(tenant.out, tenant.out, target)\n",
         "        dest = tenant.locate_for_write(tenant.out, tenant.out, rel)\n"
         "        target = tenant.hooks.output_path(rel)\n"
         "        if target != rel:\n"
         "            dest = sitepath.join(tenant.out, target)\n"),
    ]),
    ("m6_asset_folded_lookup_unchecked", [
        ("assets.py",
         "        current = tenant.contained(os.path.join(current, match))\n",
         "        current = os.path.join(current, match)\n"),
    ]),
    ("m7_tenant_name_not_canonical", [
        ("tenants.py",
         "    if not NAME_RE.match(name) or not sitepath.is_plain_name(name):\n",
         "    if not NAME_RE.match(name) or name in (\".\", \"..\"):\n"),
    ]),
    ("m8_export_catalog_shared", [
        ("archive.py",
         "    _catalog[(tenant.root, name)] = Catalogued(dest, len(data), listing)\n",
         "    _catalog[name] = Catalogued(dest, len(data), listing)\n"),
        ("archive.py",
         "    known = _catalog.get((tenant.root, name))\n",
         "    known = _catalog.get(name)\n"),
    ]),
]


def apply(tree, edits):
    for name, old, new in edits:
        path = os.path.join(tree, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        count = text.count(old)
        if count != 1:
            raise SystemExit("%s: expected one match, found %d for %r" % (name, count, old[:60]))
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text.replace(old, new))


def fresh_copy(dest):
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(GOLD, dest, ignore=shutil.ignore_patterns("__pycache__"))


def main():
    fresh_copy(PUBLIC)
    for _vid, edits in VARIANTS:
        apply(PUBLIC, edits)
    os.makedirs(MUTANTS, exist_ok=True)
    for entry in os.listdir(MUTANTS):
        shutil.rmtree(os.path.join(MUTANTS, entry))
    for vid, edits in VARIANTS:
        dest = os.path.join(MUTANTS, vid)
        fresh_copy(dest)
        apply(dest, edits)
    print("public/src and %d mutants written" % len(VARIANTS))


if __name__ == "__main__":
    main()
