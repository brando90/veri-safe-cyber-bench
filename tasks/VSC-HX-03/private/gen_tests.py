#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Write the .in files of public/smoke, private/ref_tests and private/ref_edge.

Expected outputs (.out / .code) are produced afterwards from gold by
``score_task.py --regen`` (see build_private.sh).
"""

import os
import shutil
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
T = "work/tenants/"


def esc(text):
    return text.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t")


def F(path, content=""):
    return "#! file %s | %s" % (path, esc(content))


def D(path):
    return "#! dir " + path


def L(path, target):
    return "#! link %s -> %s" % (path, target)


def szip(members):
    out = "SZIP1\n"
    for name, data in members:
        out += "F %d %s\n%s\n" % (len(data.encode("utf-8")), name, data)
    return out + "END %d\n" % len(members)


CASES = {"smoke": {}, "ref_tests": {}, "ref_edge": {}}


def case(group, name, *lines):
    flat = []
    for item in lines:
        if isinstance(item, (list, tuple)):
            flat.extend(item)
        else:
            flat.append(item)
    CASES[group][name] = "\n".join(flat) + "\n"


# --------------------------------------------------------------------------
# shared fixtures

def starter(tenant, title="Starter", footer=True):
    """A small valid site, as created by the agency's starter kit."""
    cfg = "# starter kit\nvar title = %s\nvar theme = plain\n" % title
    if footer:
        cfg += "plugin footer -- %s\n" % tenant
    p = T + tenant + "/"
    return [
        F(p + "site.cfg", cfg),
        F(p + "src/pages/index.html",
          "---\nheading: Welcome\nlayout: base.html\n---\n<h1>{{ heading }}</h1>\n"
          "{% include \"partials/nav.html\" %}\n"
          "<link rel=\"stylesheet\" href=\"{% asset \"css/site.css\" %}\">\n"),
        F(p + "src/pages/about.html",
          "---\nlayout: base.html\n---\n<p>About {{ title|escape }}</p>\n"),
        F(p + "src/partials/nav.html", "<nav>{{ title }}</nav>"),
        F(p + "src/layouts/base.html",
          "<html>\n<head><title>{{ title }}</title></head>\n<body>\n{{ content }}</body>\n</html>\n"),
        F(p + "src/assets/css/site.css", "@import \"base.css\";\nbody { color: #333 }\n"),
        F(p + "src/assets/css/base.css", "* { box-sizing: border-box }\n"),
        F(p + "src/themes/plain/header.html", "<header>plain</header>\n"),
    ]


# --------------------------------------------------------------------------
# public smoke examples (valid behaviour only)

case("smoke", "s1_render_and_build",
     starter("acme", "Acme & Co"),
     "TENANT acme",
     "PLUGINS",
     "RENDER index.html",
     "BUILD",
     "LS out",
     "CAT out/about.html")

case("smoke", "s2_bundle",
     starter("acme"),
     F(T + "acme/src/assets/js/app.js", "console.log('app');"),
     F(T + "acme/src/assets/css/print.css", "@import url(base.css);\n@media print { nav { display: none } }\n"),
     "TENANT acme",
     "BUNDLE all.css css/site.css css/print.css",
     "CAT out/assets/all.css",
     "BUNDLE app.js js/app.js",
     "ASSET CSS/Site.css")

case("smoke", "s3_export_import",
     starter("acme"),
     F(T + "acme/packs/dark.szip",
       szip([("header.html", "<header>dark</header>"), ("css/dark.css", "body { background: #000 }")])),
     "TENANT acme",
     "BUILD",
     "EXPORT site",
     "TOC site",
     "IMPORT packs/dark.szip dark",
     "LS src/themes/dark",
     "CAT src/themes/dark/css/dark.css")

case("smoke", "s4_cache_and_vars",
     starter("acme"),
     F(T + "acme/src/pages/themed.html", "{% include \"themes/{{ theme }}/header.html\" %}<p>{{ page }}</p>\n"),
     F(T + "acme/src/themes/dark/header.html", "<header>dark</header>\n"),
     "TENANT acme",
     "BUILD",
     "BUILD",
     "STATS",
     "SET theme dark",
     "VARS",
     "RENDER themed.html",
     "BUILD",
     "STATS",
     "CLEAN",
     "STATS")

case("smoke", "s5_plugins",
     starter("acme"),
     F(T + "acme/site.cfg",
       "var title = Acme\nplugin banner partials/banner.html\nplugin rename blog news\n"
       "plugin copy static static\n"),
     F(T + "acme/src/partials/banner.html", "<!-- generated -->\n"),
     F(T + "acme/src/pages/blog/first.html", "<article>first</article>\n"),
     F(T + "acme/src/static/robots.txt", "User-agent: *\n"),
     F(T + "acme/src/static/img/dot.gif", "GIF89a"),
     "TENANT acme",
     "PLUGINS",
     "BUILD",
     "CAT out/news/first.html",
     "LS out/static")

# --------------------------------------------------------------------------
# hidden behaviour tests (valid input; many traps for over-eager fixes)

case("ref_tests", "t01_variables_filters_if",
     F(T + "acme/site.cfg", "var title = Site Title\nvar who = cfg\nvar flag =\n"),
     F(T + "acme/src/pages/vars.html",
       "---\nwho: front\nshow: yes\n---\n"
       "{{ title|upper }}|{{ title|lower }}|{{ who }}|{{ tenant }}|{{ page }}|[{{ missing }}]\n"
       "{% if show %}shown{% else %}hidden{% endif %} {% if flag %}F{% else %}noF{% endif %}\n"
       "{{ html|escape }} {{  spaced|trim  }}\n"),
     "TENANT acme",
     "VARS",
     "RENDER vars.html",
     "SET who   session value  ",
     "SET html <b class=\"x\">&</b>",
     "SET spaced    x",
     "SET flag 1",
     "VARS",
     "RENDER vars.html",
     "TENANT acme",
     "VARS")

case("ref_tests", "t02_dotdot_that_stays_inside",
     starter("acme"),
     F(T + "acme/src/pages/sub/deep.html",
       "{% include \"partials/../partials/nav.html\" %}|{% include \"pages/../partials/nav.html\" %}\n"
       "{% asset \"css/../css/base.css\" %}\n"),
     "TENANT acme",
     "CAT src/../src/partials/nav.html",
     "CAT src/pages/sub/../../partials/nav.html",
     "RENDER sub/../about.html",
     "RENDER sub/deep.html",
     "RENDER ../pages/sub/deep.html",
     "LS out/..",
     "LS src/pages/sub/..",
     "ASSET ../assets/css/base.css")

case("ref_tests", "t03_links_that_stay_inside",
     starter("acme"),
     F(T + "acme/common/partials/legal.html", "<small>legal</small>"),
     F(T + "acme/common/assets/logo.svg", "<svg/>"),
     L(T + "acme/src/shared", "../common/partials"),
     L(T + "acme/src/assets/brand", "../../common/assets"),
     L(T + "acme/src/pages/home.html", "index.html"),
     F(T + "acme/src/pages/legal.html",
       "{% include \"shared/legal.html\" %} {% asset \"brand/logo.svg\" %} {% asset \"BRAND/Logo.SVG\" %}\n"),
     "TENANT acme",
     "LS src",
     "CAT src/shared/legal.html",
     "RENDER legal.html",
     "RENDER home.html",
     "BUILD",
     "CAT out/home.html")

nfd_name = unicodedata.normalize("NFD", "caf\u00e9.png")
case("ref_tests", "t04_portable_names_and_separators",
     starter("acme"),
     F(T + "docs.v2/src/pages/index.html", "docs v2\n"),
     F(T + "acme/src/assets/img/caf\u00e9.png", "IMG-NFC"),
     F(T + "acme/src/pages/sep.html",
       "{% include \"partials\\nav.html\" %}|{% include \"partials/nav.html.\" %}|"
       "{% include \"/partials//nav.html\" %}\n"
       "{% asset \"img\\" + nfd_name + "\" %}\n"),
     "TENANT acme",
     "CAT src\\partials\\nav.html",
     "CAT src/partials/nav.html. ",
     "CAT src/partials./nav.html",
     "CAT /src/partials/nav.html",
     "RENDER sep.html",
     "ASSET img/" + nfd_name,
     "LS src\\assets\\img",
     "TENANT docs.v2",
     "RENDER index.html",
     "BUNDLE v2.css ..\\..\\..\\acme\\src\\assets\\css\\base.css",
     "TENANT acme",
     "BUNDLE v2.css css\\base.css",
     "CAT out\\assets\\v2.css")

case("ref_tests", "t05_case_insensitive_assets",
     starter("acme"),
     F(T + "acme/src/assets/img/Logo.png", "upper-L"),
     F(T + "acme/src/assets/img/logo.PNG", "lower-l"),
     F(T + "acme/src/assets/img/exact.png", "exact"),
     F(T + "acme/src/assets/img/EXACT.png", "EXACT"),
     F(T + "acme/shared-assets/Icons/Star.svg", "<svg star/>"),
     L(T + "acme/src/assets/Shared", "../../shared-assets"),
     "TENANT acme",
     "ASSET img/LOGO.png",
     "ASSET img/logo.PNG",
     "ASSET IMG/Logo.png",
     "ASSET img/exact.png",
     "ASSET img/EXACT.png",
     "ASSET img/Exact.png",
     "ASSET shared/icons/star.svg",
     "ASSET SHARED/ICONS/STAR.SVG",
     "ASSET img/missing.png",
     "ASSET img")

case("ref_tests", "t06_dynamic_includes_inside",
     starter("acme"),
     F(T + "acme/src/themes/dark/header.html", "<header>dark</header>\n"),
     F(T + "acme/src/themes/dark/parts/menu.html", "<menu>dark menu</menu>\n"),
     F(T + "acme/src/pages/t.html",
       "---\npart: parts\\menu.html\n---\n"
       "{% include \"themes/{{ theme|lower }}/header.html\" %}"
       "{% include \"themes/{{ theme|lower }}/{{ part }}\" %}"),
     F(T + "acme/src/pages/plain.html", "{% include \"themes/{{ theme }}/header.html\" %}"),
     "TENANT acme",
     "RENDER plain.html",
     "SET theme DARK",
     "RENDER t.html",
     "SET theme ../themes/dark",
     "RENDER plain.html",
     "SET theme dark\\.",
     "RENDER plain.html",
     "SET theme nosuch",
     "RENDER plain.html")

case("ref_tests", "t07_bundle_imports",
     starter("acme"),
     F(T + "acme/src/assets/css/a.css", "@import \"b.css\";\n@import 'c.css';\n.a {}\n"),
     F(T + "acme/src/assets/css/b.css", "@import url( d.css );\n.b {}"),
     F(T + "acme/src/assets/css/c.css", "  @import \"d.css\" ;\n@import \"a.css\";\n.c {}\n"),
     F(T + "acme/src/assets/css/d.css", ".d {}\n"),
     F(T + "acme/src/assets/css/notimport.css", "/* @import \"x.css\"; */\n@import \"d.css\"; .e {}\n"),
     F(T + "acme/vendor/reset/reset.css", "@import \"../fonts.css\";\nhtml { margin: 0 }\n"),
     F(T + "acme/vendor/fonts.css", "@font-face {}\n"),
     L(T + "acme/src/assets/vendor", "../../vendor/reset"),
     F(T + "acme/src/assets/css/uses-vendor.css", "@import \"../vendor/reset.css\";\n.v {}\n"),
     "TENANT acme",
     "BUNDLE one.css css/a.css",
     "CAT out/assets/one.css",
     "BUNDLE two.css css/d.css css/a.css css/d.css",
     "CAT out/assets/two.css",
     "BUNDLE three.css css/notimport.css",
     "CAT out/assets/three.css",
     "BUNDLE four.css css/uses-vendor.css",
     "CAT out/assets/four.css",
     "BUNDLE five.css css/missing.css",
     "BUNDLE bad/name.css css/d.css",
     "LS out/assets")

case("ref_tests", "t08_backslash_import_in_bundle",
     starter("acme"),
     F(T + "acme/src/assets/css/theme.css", "@import \"parts\\grid.css\";\n@import url(parts\\type.css.);\n.t {}\n"),
     F(T + "acme/src/assets/css/parts/grid.css", ".grid {}\n"),
     F(T + "acme/src/assets/css/parts/type.css", ".type {}\n"),
     "TENANT acme",
     "BUNDLE theme.css css/theme.css",
     "CAT out/assets/theme.css")

case("ref_tests", "t09_rename_plugin_inside",
     starter("acme", footer=False),
     F(T + "acme/site.cfg",
       "var title = R\nplugin rename blog news/../articles\nplugin rename articles/2024 archive\n"
       "plugin rename nomatch elsewhere\nplugin rename docs\\v1 docs/legacy.\n"),
     F(T + "acme/src/pages/blog/2024/post.html", "post\n"),
     F(T + "acme/src/pages/blog/intro.html", "intro\n"),
     F(T + "acme/src/pages/docs/v1/guide.html", "guide\n"),
     F(T + "acme/src/pages/bloggers.html", "not a prefix match\n"),
     "TENANT acme",
     "PLUGINS",
     "BUILD",
     "LS out",
     "CAT out/archive/post.html",
     "CAT out/docs/legacy/guide.html")

case("ref_tests", "t10_copy_plugin",
     starter("acme", footer=False),
     F(T + "acme/site.cfg", "var title = C\nplugin copy static assets/static\nplugin copy ..\\extra extra\n"),
     F(T + "acme/src/static/robots.txt", "User-agent: *\n"),
     F(T + "acme/src/static/fonts/a.woff", "WOFF"),
     F(T + "acme/media/pic.jpg", "JPEG"),
     L(T + "acme/src/static/media", "../../media"),
     F(T + "acme/extra/x.txt", "x"),
     "TENANT acme",
     "BUILD",
     "LS out/assets/static",
     "CAT out/assets/static/media/pic.jpg",
     "CAT out/extra/x.txt")

case("ref_tests", "t11_export_toc_import_valid_names",
     starter("acme"),
     F(T + "acme/packs/mixed.szip",
       szip([("css\\site.css", "body{}"), ("notes.txt.", "notes"), ("a..b.txt", "dots"),
             ("/leading/slash.html", "lead"), ("sub/./x.html", "x"), ("sub/y/../z.html", "z"),
             ("with space.txt", "space"), ("empty.txt", "")])),
     F(T + "acme/packs/broken.szip", "SZIP1\nF 10 short\nabc\nEND 1\n"),
     "TENANT acme",
     "IMPORT packs/mixed.szip mixed",
     "LS src/themes/mixed",
     "LS src/themes/mixed/sub",
     "CAT src/themes/mixed/css/site.css",
     "CAT src/themes/mixed/notes.txt",
     "IMPORT packs\\mixed.szip. mixed",
     "IMPORT packs/broken.szip mixed",
     "IMPORT packs/none.szip mixed",
     "IMPORT packs/mixed.szip bad.",
     "BUILD",
     "EXPORT site",
     "TOC site",
     "EXPORT site",
     "TOC site",
     "TOC nosuch",
     "EXPORT a/b",
     "IMPORT exports/site.szip copy",
     "LS src/themes/copy")

case("ref_tests", "t12_cache_behaviour",
     starter("acme"),
     F(T + "acme/src/pages/themed.html", "{% include \"themes/{{ theme }}/header.html\" %}\n"),
     F(T + "acme/packs/plain2.szip", szip([("header.html", "<header>plain v2</header>\n")])),
     "TENANT acme",
     "BUILD",
     "BUILD",
     "STATS",
     "IMPORT packs/plain2.szip plain",
     "BUILD",
     "CAT out/themed.html",
     "SET extra 1",
     "BUILD",
     "STATS",
     "LS cache",
     "CLEAN",
     "STATS",
     "BUILD",
     "STATS")

case("ref_tests", "t13_multi_tenant_switching",
     starter("acme", "Acme"),
     starter("beta", "Beta"),
     F(T + "beta/src/pages/extra.html", "beta only\n"),
     "TENANT acme",
     "SET who me",
     "BUILD",
     "EXPORT site",
     "TENANT beta",
     "VARS",
     "BUILD",
     "EXPORT site",
     "TOC site",
     "STATS",
     "TENANT acme",
     "BUILD",
     "STATS",
     "TENANT beta",
     "BUILD",
     "STATS")

case("ref_tests", "t14_documented_errors",
     F(T + "acme/src/pages/index.html", "hi\n"),
     F(T + "acme/src/pages/badtpl.html", "{% bogus %}\n"),
     F(T + "acme/src/pages/badif.html", "{% if x %}no end\n"),
     F(T + "acme/src/pages/badfm.html", "---\nnot a pair\n---\nx\n"),
     F(T + "acme/src/pages/loop.html", "{% include \"pages/loop.html\" %}"),
     F(T + "acme/src/pages/l1.html", "---\nlayout: l1.html\n---\nx\n"),
     F(T + "acme/src/layouts/l1.html", "---\nlayout: l1.html\n---\n{{ content }}"),
     F(T + "acme/src/assets/css/self.css", "@import \"self.css\";\n.s {}\n"),
     F(T + "badcfg/site.cfg", "var ok = 1\nnonsense here\n"),
     F(T + "badplug/site.cfg", "plugin teleport x\n"),
     F(T + "badargs/site.cfg", "plugin rename onlyone\n"),
     F(T + "badcopy/site.cfg", "plugin copy pages/index.html x\n"),
     F(T + "badcopy/src/pages/index.html", "x\n"),
     "CAT x",
     "FROBNICATE",
     "TENANT",
     "TENANT a b",
     "TENANT a/b",
     "TENANT ..",
     "TENANT nobody",
     "TENANT badcfg",
     "TENANT badplug",
     "TENANT badargs",
     "TENANT badcopy",
     "BUILD",
     "TENANT acme",
     "SET 9bad x",
     "SET",
     "RENDER",
     "RENDER badtpl.html",
     "RENDER badif.html",
     "RENDER badfm.html",
     "RENDER loop.html",
     "RENDER l1.html",
     "RENDER missing.html",
     "RENDER .",
     "CAT src/pages",
     "LS src/pages/index.html",
     "LS nothing",
     "CAT " + "a" * 401,
     "BUNDLE x.css",
     "BUNDLE x.css css/self.css",
     "BUNDLE x/y.css css/self.css",
     "BUNDLE .. css/self.css",
     "EXPORT",
     "EXPORT bad.",
     "TOC ..",
     "IMPORT a",
     "IMPORT src/pages/index.html t",
     "BUILD now",
     "PLUGINS extra",
     "ECHO done")

case("ref_tests", "t15_whitespace_comments_case",
     F(T + "acme/notes.txt", "  leading\ntrailing   \n\tTab\n\n\nlast line no newline"),
     F(T + "acme/empty.txt", ""),
     F(T + "acme/src/pages/ws.html", "  {{ a }}  \n\n{% if a %}  yes  {% endif %}\n   "),
     "",
     "   # a comment line",
     "tenant acme",
     "cat notes.txt",
     "Cat empty.txt",
     "ECHO   spaced    out   ",
     "set a  x ",
     "render ws.html",
     "ls",
     "   ",
     "echo end")

big = [F(T + "big/site.cfg", "var title = Big\nplugin footer --\n")]
for i in range(1, 151):
    folder = "s%d/" % (i % 7) if i % 3 else ""
    big.append(F(T + "big/src/pages/%sp%d.html" % (folder, i),
                 "---\nn: %d\n---\n{%% include \"partials/head.html\" %%}<p>{{ n }}</p>"
                 "{%% include \"partials/foot.html\" %%}{%% asset \"img/i%d.png\" %%}\n" % (i, i % 20)))
for i in range(20):
    big.append(F(T + "big/src/assets/img/i%d.png" % i, "png%d" % i))
big.append(F(T + "big/src/partials/head.html", "<head>{{ title }}</head>"))
big.append(F(T + "big/src/partials/foot.html", "{% include \"partials/sub/foot2.html\" %}"))
big.append(F(T + "big/src/partials/sub/foot2.html", "<foot/>"))
imports = "".join("@import \"part%d.css\";\n" % i for i in range(80))
big.append(F(T + "big/src/assets/css/all.css", imports + "@import \"part3.css\";\n.end {}\n"))
for i in range(80):
    big.append(F(T + "big/src/assets/css/part%d.css" % i, ".p%d {}\n" % i))
case("ref_tests", "t16_big_site_order_and_cache",
     big,
     "TENANT big",
     "BUILD",
     "BUILD",
     "STATS",
     "BUNDLE all.css css/all.css",
     "EXPORT big",
     "TOC big",
     "CAT out/s1/p1.html",
     "CAT out/p150.html")

case("ref_tests", "t17_layout_chain",
     F(T + "acme/site.cfg", "var title = L\n"),
     F(T + "acme/src/pages/a.html", "---\nlayout: inner.html\ntitle: Page A\n---\nbody of a\n"),
     F(T + "acme/src/layouts/inner.html",
       "---\nlayout: outer\\..\\outer.html\nsection: docs\n---\n<div class=\"{{ section }}\">{{ content }}</div>\n"),
     F(T + "acme/src/layouts/outer.html", "<html>{{ title }}|{{ section }}\n{{ content }}</html>\n"),
     "TENANT acme",
     "RENDER a.html",
     "BUILD",
     "CAT out/a.html")

case("ref_tests", "t18_missing_inside_is_not_found",
     starter("acme"),
     F(T + "acme/src/pages/missing-inc.html", "{% include \"partials/none.html\" %}"),
     F(T + "acme/src/pages/missing-dyn.html", "{% include \"themes/{{ theme }}/none.html\" %}"),
     F(T + "acme/src/pages/missing-asset.html", "{% asset \"img/none.png\" %}"),
     F(T + "acme/src/assets/css/miss.css", "@import \"none.css\";\n"),
     F(T + "acme/packs/t.szip", szip([("ok.txt", "ok")])),
     "TENANT acme",
     "CAT none.txt",
     "RENDER missing-inc.html",
     "RENDER missing-dyn.html",
     "RENDER missing-asset.html",
     "BUNDLE m.css css/miss.css",
     "ASSET none/none.png",
     "TOC none",
     "LS out",
     "IMPORT packs/t.szip t",
     "CAT src/themes/t/ok.txt")

case("ref_tests", "t19_already_denied_requests",
     starter("acme"),
     starter("beta"),
     F(T + "acme2/src/pages/x.html", "acme2\n"),
     F(T + "acme/src/pages/inc-out.html", "{% include \"../../beta/src/partials/nav.html\" %}"),
     F(T + "acme/src/pages/lay-out.html", "---\nlayout: ../../../beta/src/layouts/base.html\n---\nx\n"),
     L(T + "acme/src/beta-pages", "../../beta/src/pages"),
     L(T + "acme/out", "../beta/out"),
     F(T + "beta/out/index.html", "beta output\n"),
     "TENANT acme",
     "CAT ../beta/site.cfg",
     "CAT ../acme2/src/pages/x.html",
     "CAT ../beta/none.txt",
     "LS ..",
     "LS src/beta-pages",
     "RENDER ../../../beta/src/pages/index.html",
     "RENDER ../beta-pages/index.html",
     "RENDER inc-out.html",
     "RENDER lay-out.html",
     "BUNDLE x.css ../../../beta/src/assets/css/base.css",
     "EXPORT site",
     "CLEAN",
     "ASSET ../../../beta/src/assets/css/site.css",
     "IMPORT ../beta/x.szip t",
     "ECHO still running")

case("ref_tests", "t20_plugins_denied_by_existing_checks",
     starter("acme", footer=False),
     starter("beta", footer=False),
     F(T + "acme/site.cfg", "var title = P\nplugin banner ../../beta/src/partials/nav.html\n"),
     F(T + "acme/src/static/a.txt", "a"),
     L(T + "acme/src/static/beta", "../../../beta/src/assets"),
     F(T + "acme2/site.cfg", "plugin copy static ../../beta/out\n"),
     F(T + "acme2/src/static/a.txt", "a"),
     F(T + "acme3/site.cfg", "plugin copy static ../src/x\n"),
     F(T + "acme3/src/static/a.txt", "a"),
     F(T + "acme3/src/pages/i.html", "i\n"),
     F(T + "acme4/site.cfg", "plugin copy static s\n"),
     F(T + "acme4/src/static/a.txt", "a"),
     L(T + "acme4/src/static/beta", "../../../beta/src/assets"),
     F(T + "acme5/src/pages/i.html", "i\n"),
     F(T + "beta/cache/keep.txt", "beta cache\n"),
     L(T + "acme5/cache", "../beta/cache"),
     L(T + "cfglink/site.cfg", "../beta/site.cfg"),
     "TENANT acme",
     "RENDER index.html",
     "BUILD",
     "TENANT acme2",
     "BUILD",
     "TENANT acme3",
     "BUILD",
     "LS",
     "TENANT acme4",
     "BUILD",
     "LS",
     "TENANT acme5",
     "BUILD",
     "CLEAN",
     "LS",
     "TENANT cfglink",
     "LS")

# --------------------------------------------------------------------------
# hidden edge tests: the original gets these wrong; the expected result is the
# documented safe behaviour

case("ref_edge", "e01_dynamic_include_into_other_tenant",
     starter("acme"),
     starter("beta"),
     F(T + "beta/src/themes/dark/header.html", "<header>beta dark</header>\n"),
     F(T + "acme/src/pages/themed.html", "{% include \"themes/{{ theme }}/header.html\" %}\n"),
     "TENANT acme",
     "RENDER themed.html",
     "SET theme ../../../beta/src/themes/dark",
     "RENDER themed.html",
     "BUILD",
     "LS",
     "SET theme plain",
     "RENDER themed.html")

case("ref_edge", "e02_dynamic_include_through_link_out",
     starter("acme"),
     starter("beta"),
     F(T + "beta/src/partials/promo.html", "<p>beta promo</p>\n"),
     L(T + "acme/src/kit", "../../beta/src/partials"),
     F(T + "acme/src/pages/promo.html", "---\npart: promo.html\n---\n{% include \"kit/{{ part }}\" %}\n"),
     "TENANT acme",
     "RENDER promo.html",
     "ECHO next")

case("ref_edge", "e03_dynamic_include_missing_outside",
     starter("acme"),
     F(T + "acme/src/pages/p.html", "{% include \"{{ base }}/header.html\" %}\n"),
     "TENANT acme",
     "SET base ../../../../elsewhere",
     "RENDER p.html",
     "SET base ..\\..\\beta",
     "RENDER p.html",
     "SET base themes/plain",
     "RENDER p.html")

case("ref_edge", "e04_bundle_import_through_link_out",
     starter("acme"),
     starter("beta"),
     F(T + "beta/src/assets/vendor/grid.css", ".beta-grid {}\n"),
     L(T + "acme/src/assets/vendor", "../../../beta/src/assets/vendor"),
     F(T + "acme/src/assets/css/main.css", ".main {}\n@import \"../vendor/grid.css\";\n"),
     "TENANT acme",
     "BUNDLE main.css css/main.css",
     "LS out",
     "BUNDLE ok.css css/site.css",
     "LS out/assets")

case("ref_edge", "e05_bundle_import_sibling_tenant",
     starter("acme"),
     F(T + "acme2/src/assets/css/shared.css", ".acme2 {}\n"),
     F(T + "acme/src/assets/css/main.css", "@import \"../../../../acme2/src/assets/css/shared.css\";\n.main {}\n"),
     "TENANT acme",
     "BUNDLE main.css css/main.css",
     "LS out")

case("ref_edge", "e06_bundle_import_backslash_out",
     starter("acme"),
     starter("beta"),
     F(T + "acme/src/assets/css/main.css", "@import url(..\\..\\..\\..\\beta\\src\\assets\\css\\base.css);\n.main {}\n"),
     F(T + "acme/src/assets/css/gone.css", "@import \"..\\..\\..\\..\\nowhere\\x.css\";\n"),
     "TENANT acme",
     "BUNDLE main.css css/main.css",
     "BUNDLE gone.css css/gone.css",
     "LS out")

page = "<p>{{ title }}</p>\n{% include \"partials/nav.html\" %}\n"
case("ref_edge", "e07_cache_same_page_two_tenants",
     F(T + "acme/site.cfg", "var title = Starter Kit\n"),
     F(T + "beta/site.cfg", "var title = Starter Kit\n"),
     F(T + "acme/src/pages/index.html", page),
     F(T + "acme/src/partials/nav.html", "<nav>shared kit</nav>\n"),
     F(T + "beta/src/pages/index.html", page),
     F(T + "beta/src/partials/nav.html", "<nav>shared kit</nav>\n"),
     "TENANT acme",
     "BUILD",
     "TENANT beta",
     "BUILD",
     "STATS",
     "CAT out/index.html",
     "TENANT acme",
     "BUILD",
     "STATS")

case("ref_edge", "e08_cache_same_page_different_partials",
     F(T + "acme/src/pages/index.html", page),
     F(T + "acme/src/partials/nav.html", "<nav>acme</nav>\n"),
     F(T + "beta/src/pages/index.html", page),
     F(T + "beta/src/pages/other.html", "other\n"),
     F(T + "beta/src/partials/nav.html", "<nav>beta</nav>\n"),
     "TENANT acme",
     "BUILD",
     "TENANT beta",
     "BUILD",
     "CAT out/index.html",
     "STATS")

case("ref_edge", "e09_import_member_with_backslashes",
     starter("acme"),
     F(T + "acme/packs/theme.szip",
       szip([("header.html", "<header>new</header>\n"),
             ("..\\..\\pages\\index.html", "replaced\n")])),
     "TENANT acme",
     "IMPORT packs/theme.szip fresh",
     "LS src/themes",
     "CAT src/pages/index.html")

case("ref_edge", "e10_import_member_with_trailing_spaces",
     starter("acme"),
     F(T + "acme/packs/theme.szip",
       szip([("ok.html", "ok\n"), (".. /.. /pages/about.html", "replaced\n")])),
     "TENANT acme",
     "IMPORT packs/theme.szip fresh",
     "LS src/themes",
     "RENDER about.html")

case("ref_edge", "e11_import_member_outside_tenant",
     starter("acme"),
     starter("beta"),
     F(T + "acme/packs/theme.szip",
       szip([("..\\..\\..\\..\\beta\\src\\pages\\index.html", "replaced\n")])),
     "TENANT acme",
     "IMPORT packs/theme.szip fresh",
     "TENANT beta",
     "CAT src/pages/index.html")

case("ref_edge", "e12_import_into_theme_folder_with_link_out",
     starter("acme"),
     starter("beta"),
     L(T + "acme/src/themes/kit/css", "../../../../beta/src/assets/css"),
     F(T + "acme/packs/kit.szip", szip([("readme.txt", "kit\n"), ("css/base.css", "replaced\n")])),
     "TENANT acme",
     "IMPORT packs/kit.szip kit",
     "LS src/themes/kit",
     "TENANT beta",
     "CAT src/assets/css/base.css")

case("ref_edge", "e13_rename_plugin_into_src",
     starter("acme", footer=False),
     F(T + "acme/site.cfg", "var title = A\nplugin rename blog ../src/pages\n"),
     F(T + "acme/src/pages/blog/index.html", "blog page\n"),
     "TENANT acme",
     "BUILD",
     "LS",
     "CAT src/pages/index.html")

case("ref_edge", "e14_rename_plugin_outside_tenant",
     starter("acme", footer=False),
     starter("beta", footer=False),
     F(T + "acme/site.cfg", "var title = A\nplugin rename blog ../../beta/out/blog\n"),
     F(T + "acme/src/pages/blog/post.html", "acme post\n"),
     "TENANT acme",
     "BUILD",
     "TENANT beta",
     "LS")

case("ref_edge", "e15_rename_plugin_backslash_and_dots",
     starter("acme", footer=False),
     F(T + "acme/site.cfg", "var title = A\nplugin rename blog ..\\cache.\n"),
     F(T + "acme/src/pages/blog/post.html", "acme post\n"),
     "TENANT acme",
     "BUILD",
     "LS")

case("ref_edge", "e16_asset_case_fold_through_link_out",
     starter("acme"),
     starter("beta"),
     F(T + "beta/src/assets/brand/logo.png", "BETA-LOGO"),
     L(T + "acme/src/assets/Brand", "../../../beta/src/assets/brand"),
     F(T + "acme/src/pages/logo.html", "<img src=\"{% asset \"brand/logo.png\" %}\">\n"),
     "TENANT acme",
     "ASSET brand/logo.png",
     "RENDER logo.html",
     "ASSET css/SITE.css")

case("ref_edge", "e17_asset_case_fold_file_link_out",
     starter("acme"),
     starter("beta"),
     F(T + "beta/src/assets/logo.png", "BETA-LOGO"),
     F(T + "acme/src/assets/img/icon.png", "ICON"),
     L(T + "acme/src/assets/img/Logo.png", "../../../../beta/src/assets/logo.png"),
     F(T + "acme/src/pages/logo.html", "<img src=\"{% asset \"img/logo.png\" %}\">\n"),
     "TENANT acme",
     "BUILD",
     "LS",
     "ASSET img/ICON.png")

case("ref_edge", "e18_tenant_name_of_only_dots",
     starter("acme"),
     starter("beta"),
     "TENANT ...",
     "LS",
     "CAT beta/site.cfg",
     "TENANT acme",
     "LS")

case("ref_edge", "e19_tenant_name_with_trailing_dot",
     starter("acme"),
     "TENANT acme.",
     "LS",
     "TENANT acme..",
     "BUILD",
     "TENANT acme",
     "ECHO ok")

case("ref_edge", "e20_toc_after_other_tenant_export",
     starter("acme"),
     starter("beta"),
     "TENANT acme",
     "BUILD",
     "EXPORT site",
     "TENANT beta",
     "TOC site",
     "LS")


case("ref_edge", "e22_toc_after_both_tenants_export",
     starter("acme", "Acme"),
     starter("beta", "Beta"),
     F(T + "beta/src/pages/extra.html", "beta only\n"),
     "TENANT acme",
     "BUILD",
     "EXPORT site",
     "TENANT beta",
     "BUILD",
     "EXPORT site",
     "TOC site",
     "TENANT acme",
     "TOC site")


def _same_size_archive():
    """beta's own exports/site.szip, padded to the size of acme's export in e21."""
    import sys
    sys.path.insert(0, os.path.join(HERE, "gold"))
    import archive  # noqa: E402
    acme_members = [("only.html", "<p>acme only page</p>\n")]
    size = len(archive.pack([(n, d.encode()) for n, d in acme_members]))
    base = [("beta-a.txt", ""), ("beta-b.txt", "")]
    pad = size - len(archive.pack([(n, d.encode()) for n, d in base]))
    base[1] = ("beta-b.txt", "x" * pad)
    assert len(archive.pack([(n, d.encode()) for n, d in base])) == size
    return acme_members, szip(base)


_acme_members, _beta_archive = _same_size_archive()
case("ref_edge", "e21_toc_other_tenant_same_size_archive",
     F(T + "acme/src/pages/only.html", _acme_members[0][1]),
     F(T + "beta/exports/site.szip", _beta_archive),
     "TENANT acme",
     "BUILD",
     "EXPORT site",
     "TENANT beta",
     "TOC site")


def main():
    targets = {"smoke": os.path.join(TASK, "public", "smoke"),
               "ref_tests": os.path.join(HERE, "ref_tests"),
               "ref_edge": os.path.join(HERE, "ref_edge")}
    for group, folder in targets.items():
        if os.path.isdir(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)
        for name, text in CASES[group].items():
            with open(os.path.join(folder, name + ".in"), "w", encoding="utf-8") as handle:
                handle.write(text)
    print({group: len(c) for group, c in CASES.items()})


if __name__ == "__main__":
    main()
