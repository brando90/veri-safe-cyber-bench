# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Label search."""
import textnorm


def find(world, query):
    needle = textnorm.fold(query)
    hits = []
    for sid in world.ships.ids():
        if needle in textnorm.fold(world.ships.get(sid).label):
            hits.append(sid)
    return hits
