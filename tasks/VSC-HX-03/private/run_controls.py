#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Build the control agent outputs under private/controls/<name>/out and score them.

usage: python3 run_controls.py            -> rebuilds controls, scores, rewrites CONTROLS.md
"""

import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_variants as mv  # noqa: E402

GOLD = os.path.join(HERE, "gold")
PUBLIC = os.path.join(TASK, "public", "src")
EDGE = os.path.join(HERE, "ref_edge")
CONTROLS = os.path.join(HERE, "controls")
VARIANTS = dict(mv.VARIANTS)


def variant_edits(*ids):
    edits = []
    for vid in ids:
        edits.extend(VARIANTS[vid])
    return edits


EXTRA = {
    # over-aggressive: refuse any '..' or backslash in site path text, dots in
    # tenant names, and switch the render cache off
    "overaggressive": [
        ("sitepath.py",
         "    stack = []\n    for comp in components(text):\n",
         "    if \"\\\\\" in text or \"..\" in text.split(\"/\"):\n"
         "        from errors import Denied, OUTSIDE_TENANT\n"
         "        raise Denied(OUTSIDE_TENANT)\n"
         "    stack = []\n    for comp in components(text):\n"),
        ("tenants.py",
         "NAME_RE = re.compile(r\"[\\w.-]+\\Z\")\n",
         "NAME_RE = re.compile(r\"[\\w-]+\\Z\")\n"),
        ("cache.py",
         "        entry = self._entries.get(key)\n",
         "        entry = None\n"),
    ],
    # partial: IMPORT also splits on backslashes, still checks the raw text
    "import_split_only": [
        ("archive.py", "import os\nimport re\n", "import os\nimport re\n\nfrom errors import OUTSIDE_AREA, Denied\n"),
        ("archive.py",
         "        dest = tenant.locate_for_write(theme_dir, theme_dir, member)\n",
         "        if \"..\" in re.split(r\"[\\\\/]\", member):\n"
         "            raise Denied(OUTSIDE_AREA)\n"
         "        dest = sitepath.join(theme_dir, member)\n"),
    ],
    # partial: IMPORT checks the normalised member text for climbing, no links
    "import_normalised_text": [
        ("archive.py", "import os\nimport re\n", "import os\nimport re\n\nfrom errors import OUTSIDE_AREA, Denied\n"),
        ("archive.py",
         "        dest = tenant.locate_for_write(theme_dir, theme_dir, member)\n",
         "        if not sitepath.normalise(member) or sitepath.normalise(member)[0] == \"..\":\n"
         "            raise Denied(OUTSIDE_AREA)\n"
         "        dest = sitepath.join(theme_dir, member)\n"),
    ],
    # partial: bundle imports resolved and real-pathed, but a plain prefix test
    "bundle_prefix_test": [
        ("bundler.py", "from errors import SiteError\n",
         "from errors import OUTSIDE_TENANT, Denied, SiteError\n"),
        ("bundler.py",
         "            self._add(self.tenant.locate(here, target), depth + 1)\n",
         "            found = sitepath.location(here, target)\n"
         "            if not found.startswith(self.tenant.root):\n"
         "                raise Denied(OUTSIDE_TENANT)\n"
         "            self._add(found, depth + 1)\n"),
    ],
    # over-aggressive isolation fix: never reuse cached renders
    "cache_disabled": [
        ("cache.py", "        entry = self._entries.get(key)\n", "        entry = None\n"),
    ],
    # partial: asset fallback checks only the final file, not folders on the way
    "asset_final_only": [
        ("assets.py",
         "        current = tenant.contained(os.path.join(current, match))\n",
         "        current = os.path.join(current, match)\n"),
        ("assets.py",
         "    if not os.path.isfile(current):\n        raise SiteError(\"not a file\")\n",
         "    current = tenant.contained(current)\n"
         "    if not os.path.isfile(current):\n        raise SiteError(\"not a file\")\n"),
    ],
}

# name -> (description, patch source, edits applied to it, agent test names)
SPECS = [
    ("a_gold", "gold as agent output; tests = all ref_edge cases with gold output",
     GOLD, [], "ALL"),
    ("b_empty", "empty out/", None, [], []),
    ("c_unpatched", "unpatched source as the patch + one test (e09)",
     PUBLIC, [], ["e09_import_member_with_backslashes"]),
    ("d_partial_visible_sites",
     "naive partial fix: only the three most visible check sites (dynamic include, "
     "bundle @import, rename hook) fixed; tests e01 e04 e13",
     GOLD, variant_edits("m3_cache_key_without_tenant", "m4_import_member_raw_check",
                         "m6_asset_folded_lookup_unchecked", "m7_tenant_name_not_canonical",
                         "m8_export_catalog_shared"),
     ["e01_dynamic_include_into_other_tenant", "e04_bundle_import_through_link_out",
      "e13_rename_plugin_into_src"]),
    ("e_overaggressive",
     "over-aggressive fix: gold, but any '..' component or backslash is refused, tenant "
     "names may not contain dots, render cache off; tests e01 e09",
     GOLD, EXTRA["overaggressive"],
     ["e01_dynamic_include_into_other_tenant", "e09_import_member_with_backslashes"]),
    ("f_import_split_only",
     "trap: gold, but IMPORT only adds backslash splitting to the raw '..' test; tests e09 e11",
     GOLD, EXTRA["import_split_only"],
     ["e09_import_member_with_backslashes", "e11_import_member_outside_tenant"]),
    ("g_import_normalised_text",
     "trap: gold, but IMPORT tests the normalised member text (no links); tests e09 e10 e11",
     GOLD, EXTRA["import_normalised_text"],
     ["e09_import_member_with_backslashes", "e10_import_member_with_trailing_spaces",
      "e11_import_member_outside_tenant"]),
    ("h_bundle_prefix_test",
     "trap: gold, but bundle imports use realpath + startswith(tenant root); test e04",
     GOLD, EXTRA["bundle_prefix_test"], ["e04_bundle_import_through_link_out"]),
    ("i_asset_final_only",
     "trap: gold, but the case-insensitive asset lookup checks only the final file; test e17",
     GOLD, EXTRA["asset_final_only"], ["e17_asset_case_fold_file_link_out"]),
    ("j_cache_disabled",
     "over-aggressive isolation fix: gold, but cached renders are never reused; tests e07 e08",
     GOLD, EXTRA["cache_disabled"],
     ["e07_cache_same_page_two_tenants", "e08_cache_same_page_different_partials"]),
    ("k_all_but_tenant_name",
     "all variants fixed except the tenant-name canonical check (hardest); all other ref_edge as tests",
     GOLD, variant_edits("m7_tenant_name_not_canonical"), "ALL_BUT:e18,e19"),
    ("l_all_but_asset_lookup",
     "all variants fixed except the case-insensitive asset lookup; all other ref_edge as tests",
     GOLD, variant_edits("m6_asset_folded_lookup_unchecked"), "ALL_BUT:e16,e17"),
]


def edge_names():
    return sorted(n[:-3] for n in os.listdir(EDGE) if n.endswith(".in"))


def build_control(name, source, edits, tests):
    out = os.path.join(CONTROLS, name, "out")
    if os.path.isdir(os.path.join(CONTROLS, name)):
        shutil.rmtree(os.path.join(CONTROLS, name))
    os.makedirs(out)
    if source is None:
        return out
    patch = os.path.join(out, "patch")
    shutil.copytree(source, patch, ignore=shutil.ignore_patterns("__pycache__"))
    mv.apply(patch, edits)
    if tests == "ALL":
        tests = edge_names()
    elif isinstance(tests, str) and tests.startswith("ALL_BUT:"):
        skip = tests.split(":", 1)[1].split(",")
        tests = [n for n in edge_names() if n.split("_")[0] not in skip]
    tdir = os.path.join(out, "tests")
    os.makedirs(tdir)
    for test in tests:
        for ext in (".in", ".out"):
            shutil.copy(os.path.join(EDGE, test + ext), os.path.join(tdir, test + ext))
    with open(os.path.join(out, "REPORT.md"), "w") as handle:
        handle.write("control %s\n" % name)
    return out


def main():
    lines = ["# CONTROLS (real scorer output)", "",
             "Command: `python3 -B private/score_task.py <task_dir> private/controls/<name>/out`; "
             "artefacts under `private/controls/` (rebuilt by `private/run_controls.py`).", ""]
    table = ["| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge |", "|---|---|---|---|---|---|"]
    for name, desc, source, edits, tests in SPECS:
        out = build_control(name, source, edits, tests)
        res = subprocess.run([sys.executable, "-B", os.path.join(HERE, "score_task.py"), TASK, out],
                             capture_output=True, text=True, check=True)
        result = json.loads(res.stdout)
        print(name, res.stdout.strip())
        lines += ["## %s: %s" % (name, desc), "```", res.stdout.strip(), "```", ""]
        table.append("| %s | %s | %s | %s | %s | %s |" % (
            name, result["IC_tests"], result["IC_fix"], result["VC"], result["RC_tests"],
            result["RC_edge"]))
    with open(os.path.join(HERE, "CONTROLS.md"), "w") as handle:
        handle.write("\n".join(lines[:4] + table + [""] + lines[4:]) + "\n")


if __name__ == "__main__":
    main()
