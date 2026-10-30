# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Background jobs.

    job submit CRED PATH [delay=DURATION] [prio=N] [q.NAME=VALUE ...]
    job cancel ID
    jobs run
    jobs list

A job is a GET of PATH on behalf of the submitting key, run by ``jobs run``
once it is due.  The key is authenticated at submission and checked again
(revoked / expired) when the job runs.  Jobs are not rate limited and do
not use the cache, but a successful run counts against the request and
egress quotas and is metered like a request.

Upstream failures (status 500 and above) are retried: after the A-th failed
attempt the job is due again ``jobs.backoff * 2**(A-1)`` later, until
``jobs.max_attempts`` attempts have failed and the job is dead.  A job
refused by a quota fails at once and is not retried.

``jobs run`` takes every job due now, in queue order (due time, then higher
priority, then submission order; a retried job keeps its submission
order), and runs them one after the other at the same instant.
"""
import gateway
import invariant
import lexer
import routes
import units
from errors import CommandError, Deny
from pqueue import PQueue


class Job:
    __slots__ = ("id", "seq", "tenant", "keyid", "path", "params", "prio", "due",
                 "attempts", "state", "submitted")

    def __init__(self, jid, tenant, keyid, path, params, prio, due, submitted):
        self.id = jid
        self.seq = None
        self.tenant = tenant
        self.keyid = keyid
        self.path = path
        self.params = params
        self.prio = prio
        self.due = due
        self.attempts = 0
        self.state = "queued"
        self.submitted = submitted


class JobRunner:
    def __init__(self, world):
        self.world = world
        self.queue = PQueue()
        self.jobs = {}
        self._ids = 0

    # ------------------------------------------------------------ submit
    def submit(self, cmd):
        w = self.world
        lexer.need(cmd, 4, 4, "job submit CRED PATH [delay=DURATION] [prio=N] [q.NAME=VALUE ...]")
        lexer.allow_opts(cmd, ("delay", "prio"), prefixes=("q.",))
        cred, path = cmd.words[2], cmd.words[3]
        if not routes.valid_path(path):
            raise CommandError("job: bad path")
        delay = units.parse_duration(cmd.opt("delay", "0"), "delay")
        prio = units.parse_int(cmd.opt("prio", "0"), "prio", lo=-9, hi=9)
        params = cmd.prefixed("q.")
        try:
            key = w.keys.authenticate(cred, w.now)
        except Deny as deny:
            tenant = cred.split(".", 1)[0]
            w.audit.record(tenant if w.tenants.get(tenant) else None, "job.submit",
                           [("line", cmd.line), ("result", "deny:" + deny.code)])
            w.emit(deny.line())
            return
        self._ids += 1
        job = Job("j%d" % self._ids, key.tenant, key.keyid, routes.normalise(path), params, prio,
                  w.now + delay, w.now)
        job.seq = self.queue.push(job, job.due, job.prio)
        self.jobs[job.id] = job
        w.audit.record(job.tenant, "job.submit", [("job", job.id), ("line", cmd.line)])
        w.emit("job %s queued due=%d" % (job.id, job.due))

    def cancel(self, jid):
        job = self.jobs.get(jid)
        if job is None or job.state != "queued" or not self.queue.cancel(jid):
            raise CommandError("job: %s is not queued" % jid)
        job.state = "cancelled"
        self.world.audit.record(job.tenant, "job.cancel", [("job", jid)])
        self.world.emit("job %s cancelled" % jid)

    # ------------------------------------------------------------ run
    def run_due(self):
        w = self.world
        batch = self.queue.pop_due(w.now)
        if not batch:
            w.emit("jobs none due")
            return
        for job in batch:
            self._run_one(job)

    def _finish(self, job, state, text, fields):
        job.state = state
        self.world.audit.record(job.tenant, "job." + state, [("job", job.id)] + fields)
        self.world.outbox.notify(job.tenant, "job." + state, [("job", job.id), ("path", job.path)])
        self.world.emit("job %s %s" % (job.id, text))

    def _run_one(self, job):
        w = self.world
        now = w.now
        key = w.keys.get(job.tenant, job.keyid)
        state = key.state(now) if key is not None else "unknown-key"
        if state == "active" and w.tenants.require(job.tenant).suspended:
            state = "suspended"
        if state != "active":
            self._finish(job, "failed", "failed auth %s" % state, [("reason", "auth:" + state)])
            return
        ctx = gateway.Ctx("job", "", now)
        ctx.tenant, ctx.keyid, ctx.path, ctx.params = job.tenant, job.keyid, job.path, job.params
        ctx.attempt = job.attempts + 1
        route = routes.match("GET", job.path)
        try:
            w.quota.check_requests(ctx)
            resp = w.backend.call(ctx, route)
            if resp.status >= 500:
                self._retry(job, resp)
                return
            w.quota.check_egress(ctx, resp.nbytes)
        except Deny as deny:
            self._finish(job, "failed", "failed %s" % deny.code, [("reason", deny.code)])
            return
        job.attempts += 1
        w.quota.commit(job.tenant, resp.nbytes)
        w.meter.record(job.tenant, "job", resp.nbytes)
        invariant.after_commit(w, ctx)
        self._finish(job, "done", "done %d %dB %s" % (resp.status, resp.nbytes, resp.body),
                     [("status", resp.status), ("bytes", resp.nbytes)])

    def _retry(self, job, resp):
        w = self.world
        cfg = w.config
        job.attempts += 1
        if job.attempts >= cfg.int_value(job.tenant, "jobs.max_attempts"):
            self._finish(job, "dead", "dead attempts=%d" % job.attempts,
                         [("attempts", job.attempts), ("status", resp.status)])
            return
        delay = cfg.duration_ms(job.tenant, "jobs.backoff") * 2 ** (job.attempts - 1)
        job.due = w.now + delay
        job.seq = self.queue.push(job, job.due, job.prio, seq=job.seq)
        w.audit.record(job.tenant, "job.retry", [("job", job.id), ("attempt", job.attempts),
                                                 ("next", job.due)])
        w.emit("job %s retry attempt=%d next=%d" % (job.id, job.attempts, job.due))

    def listing(self):
        return self.queue.ordered()


def cmd_job(world, cmd):
    if len(cmd.words) < 2:
        raise CommandError("usage: job submit|cancel ...")
    sub = cmd.words[1]
    if sub == "submit":
        world.jobs.submit(cmd)
    elif sub == "cancel":
        lexer.need(cmd, 3, 3, "job cancel ID")
        lexer.allow_opts(cmd, ())
        world.jobs.cancel(cmd.words[2])
    else:
        raise CommandError("job: unknown subcommand %s" % sub)


def cmd_jobs(world, cmd):
    lexer.need(cmd, 2, 2, "jobs run|list")
    lexer.allow_opts(cmd, ())
    sub = cmd.words[1]
    if sub == "run":
        world.jobs.run_due()
    elif sub == "list":
        pending = world.jobs.listing()
        if not pending:
            world.emit("jobs none queued")
        for job in pending:
            world.emit("job %s tenant=%s path=%s due=%d prio=%d attempts=%d" % (
                job.id, job.tenant, job.path, job.due, job.prio, job.attempts))
    else:
        raise CommandError("jobs: unknown subcommand %s" % sub)
