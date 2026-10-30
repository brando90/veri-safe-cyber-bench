# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
"""Exit codes, the error message table and the two exception types."""

EXIT_OK = 0
EXIT_INVARIANT = 86

MESSAGES = {
    "usage": "usage: %s",
    "unknown_command": "unknown command '%s'",
    "bad_quoting": "unbalanced double quote",
    "dup_option": "option %s given twice",
    "bad_option": "option '%s' is not valid here",
    "unknown_customer": "unknown customer %s",
    "customer_exists": "customer %s already exists",
    "bad_id": "invalid customer id '%s'",
    "closed": "customer %s is closed",
    "already_closed": "customer %s is already closed",
    "on_hold": "customer %s is on hold",
    "open_orders": "customer %s has open orders",
    "unknown_sku": "unknown sku '%s'",
    "unknown_warehouse": "unknown warehouse '%s'",
    "unknown_category": "unknown category '%s'",
    "unknown_carrier": "unknown carrier '%s'",
    "unknown_region": "unknown region '%s'",
    "unknown_tier": "unknown tier '%s'",
    "unknown_order": "unknown order %s",
    "unknown_report": "unknown report '%s'",
    "unknown_format": "unknown export format '%s'",
    "unknown_export": "unknown export '%s'",
    "bad_number": "invalid number '%s'",
    "bad_value": "invalid value '%s'",
    "bad_yesno": "expected yes or no, got '%s'",
    "bad_line": "invalid order line '%s'",
    "bad_cond": "invalid condition '%s'",
    "bad_hour": "invalid hour '%s'",
    "line_limit": "line limit for %s is %d, got %d",
    "pack_multiple": "%s is sold in whole packs of %d, got %d",
    "restricted": "region %s does not accept hazard class %d (%s)",
    "duplicate_ref": "duplicate order reference %s",
    "not_stocked": "warehouse %s does not stock %s",
    "over_capacity": "warehouse %s is full (%d of %d units)",
    "need_expiry": "%s needs the exp= option",
    "bad_expiry": "invalid expiry day '%s'",
    "short_stock": "only %d units of %s are free at %s",
    "no_stock": "no stock of %s at %s",
    "same_warehouse": "source and destination are both %s",
    "nothing_pending": "order %s has nothing to ship or cancel",
    "no_carrier": "no carrier can take the shipment from %s to %s",
    "carrier_ineligible": "carrier %s cannot take the shipment from %s to %s",
    "lot_expired": "lot %s is expired; run expire first",
    "return_excess": "only %d units of %s can still be returned on %s",
    "return_window": "the return window for %s has closed",
    "bad_delta": "invalid adjustment '%s'",
    "carrier_region": "carrier %s does not serve region %s",
}


class CommandError(Exception):
    def __init__(self, code, *params):
        self.code = code
        self.params = params
        super().__init__(MESSAGES[code] % params)


class InvariantViolation(Exception):
    pass
