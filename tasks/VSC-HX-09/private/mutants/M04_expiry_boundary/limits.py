# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Central limits and conventions.  The README documents every value here."""

# Expression language
MAX_EXPR_CHARS = 400          # characters in one expression
MAX_TOKENS = 160              # tokens in one expression
MAX_DEPTH = 32                # nesting of (), not, [] and calls
MAX_LIST_ITEMS = 64           # items in one list literal
MAX_NUMBER = 10 ** 12         # number literals are below this

# Evaluation budgets (steps)
CHECK_STEPS = 500             # one budget per check / explain / replay
EVAL_STEPS = 500              # one budget per `eval` command
MACRO_NEST = 8                # @name calls nested at most this deep

# Approvals
MAX_TTL = 7 * 86400           # total lifetime of an approval, seconds

# Decision log
LOG_KEEP_DEFAULT = 200        # entries kept per policy set

# Secrets
MIN_SECRET_LEN = 6

# Bundles and templates
MAX_BUNDLE_LINES = 400
MAX_TEMPLATE_CHARS = 400

# Names of sets, secrets, conditions, templates and attribute keys
NAME_PATTERN = r"[a-z][a-z0-9_-]{0,31}"

# Exit status of the consistency check
INVARIANT_EXIT = 86
