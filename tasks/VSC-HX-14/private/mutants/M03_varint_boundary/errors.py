# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Exit codes, the error message table and the two exception types."""

EXIT_OK = 0
EXIT_INVARIANT = 86

MESSAGES = {
    "usage": "usage: %s",
    "unknown_command": "unknown command '%s'",
    "bad_quoting": "unbalanced double quote",
    "dup_option": "option %s given twice",
    "bad_option": "unknown option '%s' for %s",
    "bad_date": "bad date '%s'",
    "bad_start": "bad start '%s'",
    "bad_time": "bad time of day '%s'",
    "out_of_range": "date out of range",
    "bad_duration": "invalid duration '%s'",
    "bad_offset": "invalid UTC offset '%s'",
    "bad_rule": "invalid rule '%s'",
    "bad_number": "invalid number '%s'",
    "bad_unit": "invalid unit '%s'",
    "bad_title": "invalid title '%s'",
    "bad_cats": "invalid category list '%s'",
    "bad_prio": "invalid priority '%s'",
    "bad_flag": "invalid value '%s' for %s",
    "bad_id": "invalid event id '%s'",
    "bad_ref": "invalid reference '%s'",
    "unknown_event": "unknown event %s",
    "event_exists": "event %s already exists",
    "not_recurring": "event %s does not recur",
    "not_occurrence": "%s is not an occurrence of %s",
    "already_skipped": "%s is already skipped for %s",
    "not_skipped": "%s is not skipped for %s",
    "too_far": "window is too far from the start of the series",
    "window_too_big": "window is longer than %d days",
    "bad_record": "bad record '%s'",
    "bad_checksum": "checksum mismatch",
    "bad_hex": "invalid hex data",
    "seq_too_low": "sequence %s is below the next free number %s",
    "seq_exhausted": "no sequence numbers left",
    "bad_order": "FROM is after TO",
}


class CommandError(Exception):
    """A refused or malformed command.  Printed as ``error: MESSAGE``."""

    def __init__(self, code, *args):
        self.code = code
        self.params = args
        super().__init__(MESSAGES[code] % args)


class InvariantViolation(Exception):
    """The consistency check found a broken property."""
