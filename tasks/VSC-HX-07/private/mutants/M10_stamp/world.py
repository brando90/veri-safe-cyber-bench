# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""The World: one instance of every component, wired together, plus the
command table."""
import admin
import audit
import billing
import cache
import clock
import config
import gateway
import helptext
import jobs
import keys
import meter
import nonce
import plans
import quota
import ratelimit
import report
import tenants
import webhook
from backend import Backend
from errors import CommandError

COMMANDS = {
    "clock": clock.cmd_clock,
    "tenant": tenants.cmd_tenant,
    "plan": plans.cmd_plan,
    "config": config.cmd_config,
    "key": keys.cmd_key,
    "req": gateway.cmd_req,
    "job": jobs.cmd_job,
    "jobs": jobs.cmd_jobs,
    "cache": cache.cmd_cache,
    "usage": meter.cmd_usage,
    "top": meter.cmd_top,
    "bill": billing.cmd_bill,
    "audit": audit.cmd_audit,
    "check": audit.cmd_check,
    "report": report.cmd_report,
    "stats": report.cmd_stats,
    "webhook": webhook.cmd_webhook,
    "nonce": admin.cmd_nonce,
    "rate": admin.cmd_rate,
    "quota": admin.cmd_quota,
    "help": helptext.cmd_help,
}


class World:
    def __init__(self, out):
        self.out = out
        self.clock = clock.Clock()
        self.audit = audit.AuditLog(self)
        self.tenants = tenants.Tenants(self)
        self.config = config.Config(self)
        self.keys = keys.KeyStore(self)
        self.nonces = nonce.NonceStore(self)
        self.limiter = ratelimit.RateLimiter(self)
        self.quota = quota.Quota(self)
        self.cache = cache.ResponseCache(self)
        self.meter = meter.Meter(self)
        self.backend = Backend(self)
        self.gateway = gateway.Gateway(self)
        self.jobs = jobs.JobRunner(self)
        self.outbox = webhook.Outbox(self)

    @property
    def now(self):
        return self.clock.now

    def emit(self, line):
        self.out.emit(line)

    def begin_command(self):
        self.quota.begin_command(self.now)

    def dispatch(self, cmd):
        handler = COMMANDS.get(cmd.name)
        if handler is None:
            raise CommandError("unknown command %s" % cmd.name)
        handler(self, cmd)
