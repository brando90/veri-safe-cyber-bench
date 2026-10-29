# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""CSV, TSV and audit-detail formatting."""

import money
import parse

def csv_escape(text):
    """Escape CSV fields per README."""
    if ',' in text or '"' in text or '\r' in text or '\n' in text:
        return '"%s"' % text.replace('"', '""')
    return text

def tsv_escape(text):
    """Escape TSV fields per README."""
    return text.replace('\\', '\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')

def audit_detail(fields):
    """Format key="value" pairs per README."""
    parts = []
    for k, v in fields.items():
        value = str(v).replace('\\', '\\').replace('"', '\"')
        parts.append('%s="%s"' % (k, value))
    return ' '.join(parts)