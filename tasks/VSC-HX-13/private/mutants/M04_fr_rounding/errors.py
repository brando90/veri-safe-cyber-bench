# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
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
    "open_invoices": "customer %s still has unpaid invoices",
    "has_invoices": "customer %s already has invoices",
    "unknown_plan": "unknown plan '%s'",
    "same_plan": "customer %s is already on plan %s",
    "unknown_service": "unknown service '%s'",
    "unknown_region": "unknown region '%s'",
    "unknown_currency": "unknown currency '%s'",
    "unknown_kind": "unknown coupon kind '%s'",
    "unknown_coupon": "customer %s has no coupon %s",
    "unknown_invoice": "unknown invoice %s",
    "unknown_report": "unknown report '%s'",
    "unknown_format": "unknown export format '%s'",
    "unknown_export": "unknown export '%s'",
    "bad_amount": "invalid amount '%s'",
    "bad_number": "invalid number '%s'",
    "bad_value": "invalid value '%s'",
    "bad_day": "invalid day '%s'",
    "bad_yesno": "expected yes or no, got '%s'",
    "future_day": "day %d is in the future",
    "before_start": "day %d is before %s started",
    "period_invoiced": "period %d is already invoiced for %s",
    "period_open": "period %d is not closed yet",
    "no_period": "no closed period to invoice yet",
    "duplicate_usage": "duplicate usage id %s",
    "overpayment": "payment exceeds the outstanding amount of %s",
    "wrong_customer": "invoice %s does not belong to %s",
    "voided": "invoice %s is void",
    "refund_limit": "refund exceeds the net payments on %s",
    "has_payments": "invoice %s has payments",
    "bad_batch": "usage batch needs at least one quantity",
}


class CommandError(Exception):
    def __init__(self, code, *params):
        self.code = code
        self.params = params
        super().__init__(MESSAGES[code] % params)


class InvariantViolation(Exception):
    pass
