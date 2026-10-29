# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Page rendering and the BUILD pipeline.

For one page:
  1. read src/pages/<page> and split off the front matter; pre_render hooks
     (banner) may prepend text to the body
  2. variables, lowest precedence first: built-ins (tenant, page), site.cfg
     vars, front matter, SET values
  3. render the body; if the front matter names a layout, render
     src/layouts/<layout> with the same variables plus ``content`` (layouts
     may name a layout of their own, up to 4 levels)
  4. post_render hooks (footer)

BUILD renders every page below src/pages (``*.html``, sorted by path) and
then writes the results. The output path of a page is its path below
src/pages, taken relative to out/ and passed through the output_path hooks.
Nothing is written unless every page, every output path and every planned
copy has been accepted.
"""

import os

import cache
import config
import sitepath
from errors import SiteError
from template import Renderer

MAX_LAYOUT_DEPTH = 4


def discover(tenant):
    pages_dir = tenant.folder("src", "pages")
    if not os.path.isdir(pages_dir):
        return []
    return [(real, rel) for real, rel in tenant.walk_files(pages_dir)
            if rel.endswith(".html")]


def page_variables(tenant, rel, meta):
    variables = {"tenant": tenant.name, "page": rel}
    variables.update(tenant.config.variables)
    variables.update(meta)
    variables.update(tenant.session_vars)
    return variables


def render_page(tenant, rel, source, deps):
    """Rendered text of one page whose source has already been read."""
    renderer = Renderer(tenant, deps)
    meta, body = config.split_front_matter(source)
    body = tenant.hooks.pre_render(tenant, body, deps)
    variables = page_variables(tenant, rel, meta)
    output = renderer.render_text(body, variables)
    layout = meta.get("layout", "")
    depth = 0
    while layout:
        depth += 1
        if depth > MAX_LAYOUT_DEPTH:
            raise SiteError("layout too deep")
        real = tenant.locate(tenant.folder("src", "layouts"), layout)
        layout_text = tenant.read_text(real)
        deps.record(real, layout_text)
        layout_meta, layout_body = config.split_front_matter(layout_text)
        layout_vars = dict(layout_meta)
        layout_vars.update(variables)
        layout_vars["content"] = output
        output = renderer.render_text(layout_body, layout_vars)
        layout = layout_meta.get("layout", "")
    return tenant.hooks.post_render(output)


def render_one(tenant, text):
    """RENDER: the rendered text of the page named by site path ``text``."""
    pages_dir = tenant.folder("src", "pages")
    real = tenant.locate(pages_dir, text)
    source = tenant.read_text(real)
    deps = cache.Deps()
    deps.record(real, source)
    rel = sitepath.display(os.path.realpath(pages_dir), real)
    return render_page(tenant, rel, source, deps)


def build(tenant, render_cache):
    """BUILD: returns the lines to print."""
    planned = []
    fresh = []
    hits = misses = 0
    for real, rel in discover(tenant):
        source = tenant.read_text(real)
        key = cache.make_key(tenant, rel, source)
        output = render_cache.lookup(tenant, key)
        if output is None:
            deps = cache.Deps()
            deps.record(real, source)
            output = render_page(tenant, rel, source, deps)
            fresh.append((key, rel, output, deps))
            misses += 1
        else:
            hits += 1
        dest = tenant.locate_for_write(tenant.out, tenant.out, rel)
        target = tenant.hooks.output_path(rel)
        if target != rel:
            dest = sitepath.join(tenant.out, target)
        planned.append((rel, dest, output))
    copies = tenant.hooks.copy_plan(tenant)
    cache_files = render_cache.plan_files(tenant, fresh)

    lines = []
    for rel, dest, output in planned:
        tenant.guard.write_bytes(dest, output.encode("utf-8"))
        lines.append("BUILT %s -> %s" % (rel, tenant.show(dest)))
    for entries, shown in copies:
        for source_real, dest in entries:
            tenant.guard.write_bytes(dest, tenant.read_bytes(source_real))
        lines.append("COPIED %d files -> %s" % (len(entries), shown))
    render_cache.commit(tenant, fresh, cache_files, hits, misses)
    lines.append("BUILD ok: %d pages, %d cached" % (len(planned), hits))
    return lines
