# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The service registry: every rating module by code."""

import svc_storage
import svc_egress
import svc_compute
import svc_requests
import svc_sms
import svc_voice
import svc_email
import svc_logs
import svc_backup
import svc_cdn
import svc_dns
import svc_queue
import svc_search
import svc_cache
import svc_vault
import svc_metrics
import svc_ocr
import svc_geocode

MODULES = {
    "storage": svc_storage,
    "egress": svc_egress,
    "compute": svc_compute,
    "requests": svc_requests,
    "sms": svc_sms,
    "voice": svc_voice,
    "email": svc_email,
    "logs": svc_logs,
    "backup": svc_backup,
    "cdn": svc_cdn,
    "dns": svc_dns,
    "queue": svc_queue,
    "search": svc_search,
    "cache": svc_cache,
    "vault": svc_vault,
    "metrics": svc_metrics,
    "ocr": svc_ocr,
    "geocode": svc_geocode,
}


def known(code):
    return code in MODULES


def get(code):
    return MODULES[code]


def codes():
    return sorted(MODULES)
