# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Dropping old readings."""
import windows


def cutoff_for(world, now):
    """Returns the instant before which readings are dropped, or None when nothing is."""
    keep = world.config.keep_ms()
    if keep is None:
        return None
    cutoff = now - keep
    return cutoff if cutoff > 0 else None


def prune(world, now, dry=False):
    cutoff = cutoff_for(world, now)
    if cutoff is None:
        return 0
    removed = 0
    for sid in world.ships.ids():
        if dry:
            removed += len(windows.select(world.store.all(sid), 0, cutoff))
        else:
            removed += world.store.drop_before(sid, cutoff)
    return removed

