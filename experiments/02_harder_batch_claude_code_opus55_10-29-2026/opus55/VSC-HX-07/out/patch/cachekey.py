# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Response cache keys.

A key is ``SCOPE METHOD PATH?QUERY``.  The scope says who may receive the
cached response:

* ``*`` for routes whose response is the same for everybody (``shared``);
* the tenant name for routes whose response depends on the tenant;
* ``TENANT.KEYID`` for routes whose response depends on the calling key
  (key ids are only unique within a tenant).

The query is the request's ``q.`` parameters sorted by name, so the order
in which a client writes them does not matter.  ``nonce`` and ``ts`` are not
part of the request identity and never appear in a key.
"""


def scope(route, ctx):
    if route.cache == "shared":
        return "*"
    if route.cache == "key":
        return "%s.%s" % (ctx.tenant, ctx.keyid)
    return ctx.tenant


def _esc(text):
    """Escape the separators so that distinct parameter sets never share a key."""
    return (text.replace("%", "%25").replace("&", "%26").replace("=", "%3D")
            .replace(" ", "%20"))


def query(params):
    return "&".join("%s=%s" % (_esc(name), _esc(params[name])) for name in sorted(params))


def build(scope_text, method, path, params):
    return "%s %s %s?%s" % (scope_text, method, path, query(params))
