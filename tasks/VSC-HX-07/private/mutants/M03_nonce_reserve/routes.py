# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The route table of the simulated upstream service.

``cache`` is one of ``shared`` (same response for every tenant), ``tenant``
(response depends on the tenant), ``key`` (response depends on the calling
key) or ``none`` (never cached).  Paths are matched after normalisation:
repeated slashes are collapsed and a trailing slash is ignored.
"""
import re

PATH_RE = re.compile(r"/[A-Za-z0-9._/-]{0,127}\Z")


class Route:
    __slots__ = ("method", "path", "cache", "handler", "params")

    def __init__(self, method, path, cache, handler, params=()):
        self.method = method
        self.path = path
        self.cache = cache
        self.handler = handler
        self.params = params


ROUTES = (
    Route("GET", "/v1/catalog", "shared", "catalog"),
    Route("GET", "/v1/me", "key", "me"),
    Route("GET", "/v1/items", "tenant", "items_list", ("n",)),
    Route("POST", "/v1/items", "none", "items_create"),
    Route("GET", "/v1/blob", "tenant", "blob", ("size",)),
    Route("GET", "/v1/report", "none", "report", ("fail",)),
)

_BY_KEY = {(r.method, r.path): r for r in ROUTES}


def valid_path(path):
    return PATH_RE.match(path) is not None


def normalise(path):
    parts = [p for p in path.split("/") if p]
    return "/" + "/".join(parts)


def match(method, path):
    return _BY_KEY.get((method, normalise(path)))


def paths():
    return sorted({r.path for r in ROUTES})
