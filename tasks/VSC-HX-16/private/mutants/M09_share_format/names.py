# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Field-name normalisation shared by the rule table and the exporter."""

PREFIX = "x-"


def fold(name):
    """The stored form of a field name: lower case."""
    return name.lower()


def base(name):
    """The name used for matching."""
    return fold(name).removeprefix(PREFIX)


def clean_id(text):
    """A record id as typed: any number of leading # signs are ignored."""
    return text.lstrip("#")


def legacy_fold(name):
    return name.strip().lower().replace("_", "-")
