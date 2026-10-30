# quotagate

quotagate is a toy, single-process simulator of a multi-tenant API gateway.
It sits in front of a small simulated upstream service and decides, for
every request, whether the calling tenant may have it: it checks API keys,
replay protection, rate limits and quotas, serves responses from a cache,
runs background jobs with retries, meters usage, prints bills and keeps an
audit log.  Nothing here touches the network or the wall clock; time is a
logical clock that only moves when a command says so.

Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5
xhigh, 2026-10-29.

## Running

    sh build.sh                 # byte-compiles every module (syntax check)
    python3 main.py < script    # runs a command script

Python 3.12, standard library only.  The program reads commands from
standard input, one per line, and writes results to standard output.  It
exits 0 at end of input, or 86 when its consistency check fails (see
"Consistency check").

## Input format

* Blank lines and lines starting with `#` are ignored and print nothing.
* A line is split into tokens at spaces and tabs.  A double quote starts a
  quoted part that runs to the next double quote and may contain spaces;
  it is glued to the characters around it (`label="front desk"` is one
  token).  There is no escape character.
* A token `name=value` whose name is a lower-case dotted identifier
  (`ttl`, `q.size`, `rate.limit`) is an option; every other token is a word.
  Options may appear anywhere on the line; an option given twice is an error.
* A malformed command prints `error: MESSAGE` and changes nothing; the
  program carries on with the next line.

## Units

* Time is an integer number of milliseconds on the logical clock, which
  starts at 0.  A duration is written `NUMBER[ms|s|m|h|d]`; a bare number is
  milliseconds (`1500` = `1500ms` = 1.5 s).  Durations are displayed in the
  largest unit that divides them exactly (`90s`, `1500ms`, `2m`).
* A size is an integer number of bytes, written `NUMBER[B|KiB|MiB]`; a bare
  number is bytes.  1 KiB = 1024 bytes, 1 MiB = 1024 KiB.
* The request field `ts` is the client's clock in whole seconds; it is
  compared with the gateway clock in milliseconds (`ts=12` means 12000 ms).
* Money is integer millicents (`mc`, 1 cent = 1000 mc); amounts are printed
  in currency units with two decimals (`0.14`).

## Time

* The clock never moves backwards and never moves while a command runs:
  every check made during one command (including every job of one
  `jobs run` batch) sees the same instant.
* Deadlines are exclusive.  Something that is valid until T (a key that
  expires at T, a cache entry stored until T, a nonce remembered until T)
  is no longer valid at T.
* A fixed window of width W is `[k*W, (k+1)*W)` for an integer k, counted
  from time 0.  A sliding window of width W at time t is `(t-W, t]`.

## Commands

    clock | clock set TIME | clock advance DURATION      -> now=MS

    tenant add NAME [plan=PLAN]                          -> tenant NAME plan=PLAN
    tenant plan NAME PLAN | tenant suspend NAME | tenant resume NAME | tenant list
    plan list

    config set LAYER NAME VALUE                          -> config LAYER NAME=VALUE
    config load LAYER NAME=VALUE ...                     (all or nothing)
    config unset LAYER NAME
    config get TENANT NAME | config show TENANT          -> NAME=VALUE (LAYER)
    config explain TENANT NAME | config layers

    key issue TENANT KEYID secret=SECRET [ttl=DURATION] [label=TEXT]
    key revoke TENANT KEYID | key rotate TENANT KEYID secret=SECRET
    key list TENANT | key show TENANT KEYID

    req CRED METHOD PATH [nonce=N ts=S] [q.NAME=VALUE ...]

    job submit CRED PATH [delay=DURATION] [prio=N] [q.NAME=VALUE ...]
    job cancel ID | jobs run | jobs list

    cache stats | cache list | cache purge TENANT
    usage TENANT | top | bill [TENANT] | stats
    audit [TENANT] [event=EVENT] [last=N] | audit export [TENANT] format=tsv|jsonl
    report denials | report tenant TENANT
    webhook list TENANT | webhook clear TENANT
    nonce list TENANT KEYID | rate show TENANT | quota reset TENANT
    check
    help [COMMAND] | help setting NAME

Tenant names are 1 to 16 characters from `a-z 0-9 -` starting with a
letter.  Key ids are 1 to 16 characters from `a-z 0-9 _ -` starting with a
letter or digit.  Plans are `free` (the default), `basic` and `pro`.

## Configuration

Settings live in layers.  For a tenant the effective value of a setting is
taken from the strongest layer that has it: `tenant:NAME`, then
`plan:PLAN` (the tenant's current plan), then `default`.  `cache.capacity`
is global and lives only in the default layer.  `config show` lists every
setting with its effective value and the layer it came from.

| setting | kind | meaning |
|---|---|---|
| rate.mode | fixed / sliding | rate-limit window kind |
| rate.limit | integer >= 0 | accepted API requests per window |
| rate.window | duration, 1ms..1h | window width |
| quota.requests | integer >= 0 | accepted requests + job runs per quota period |
| quota.egress | size | response bytes per quota period |
| quota.period | duration, 1s..30d | quota period (fixed windows from time 0) |
| cache.ttl | duration, 0..1d | how long a response is cached (0: off) |
| cache.capacity | size | total cache capacity (global) |
| replay.window | duration, 1s..1d | how long an accepted nonce is remembered |
| replay.skew | duration, 0..1h | allowed distance between `ts` and the clock |
| replay.required | on / off | whether every request must carry a nonce |
| jobs.max_attempts | 1..10 | attempts before a failing job is dead |
| jobs.backoff | duration | base retry delay of jobs |
| price.request | integer mc | price of one API request or job run |
| price.kib | integer mc | price of one KiB of egress |
| backend.token, webhook.secret | text | sensitive (see "Secrets") |
| webhook.url | text | where job notifications would go |

**Changes take effect immediately.**  A change to any layer applies to the
very next request, job run or report of every tenant whose effective value
it changes; nothing keeps using an older value.

## Keys and credentials

A key belongs to one tenant and has a key id that is unique *within that
tenant* (two tenants may each have a key called `main`).  A client presents
the credential `TENANT.KEYID.SECRET`.  Secrets are 8 to 64 characters from
`A-Z a-z 0-9 _ -`.  A key issued at T with `ttl=D` is valid while
now < T + D; without a ttl it never expires.  Revoked keys never
authenticate again.  Requests and jobs of a suspended tenant are refused.

## Secrets

Secrets are never printed and never written to the audit log, by any
command, in any output:

* a credential is always shown as `TENANT.KEYID.***` (or `<malformed>` when
  it cannot be split that way); any text of that shape that reaches the
  output or the audit log, however it got there, has its third part masked;
* the value of a setting whose name ends in `.secret` or `.token` is shown
  as `***` wherever it appears (an empty value is shown as `""`).

Tenant names, key ids, labels, paths and nonces are not secrets.

## Requests and admission

`req CRED METHOD PATH ...` sends one request.  METHOD is GET or POST.
`q.NAME=VALUE` options are the request parameters.  `nonce=N ts=S` must be
given together.  The admission stages run in this order and the first
refusal wins:

1. authentication -> `deny auth REASON cred=TENANT.KEYID.***` where REASON
   is malformed, unknown-tenant, unknown-key, bad-secret, revoked, expired
   or suspended;
2. replay protection -> `deny nonce-required`, `deny stale`, `deny replay`;
3. rate limit -> `deny rate retry_after=SECONDS` (`deny rate` alone when
   `rate.limit` is 0);
4. request quota -> `deny quota-requests`;
5. cache lookup, or the upstream call;
6. egress quota on the response size -> `deny quota-egress`.

An accepted request prints `ok STATUS SOURCE SIZEB BODY`, where SOURCE is
`hit` (served from the cache), `miss` (cacheable, fetched upstream) or `off`
(not cacheable).  Any status the upstream returns, including 400 and 404,
is an accepted request.

**A refused request changes nothing** except that it is written to the
audit log: it does not use up its nonce, it is not counted by the rate
limit or the quotas, it is not metered and its response is not cached.

**Replay protection.**  A request with `nonce`/`ts` is fresh when the
distance between `ts` (seconds) and the clock (milliseconds) is at most
`replay.skew`, measured in milliseconds, in either direction.  A nonce
accepted at time A is remembered for the key that used it until
A + `replay.window`; the same key may not use it again while it is
remembered.  Nonces belong to a key: another key, of the same tenant or
another, may use the same nonce.  With `replay.required=on` a request
without a nonce is refused.

**Rate limit.**  Counts the tenant's accepted API requests (all of its keys
together; jobs are not counted) in the current window.  A request is
refused when that count has already reached `rate.limit`.  `retry_after` is
the time in whole seconds, rounded up, until a request would be accepted:
for fixed windows the end of the current window, for sliding windows the
moment enough of the oldest counted requests have left the window.

**Quotas.**  Per tenant and per quota period.  A request is refused when one
more request would exceed `quota.requests`, or when its response size would
take the period's egress above `quota.egress`.  Reaching a limit exactly is
allowed.  Changing `quota.period` starts a new period.

## Upstream routes

| route | cache | response |
|---|---|---|
| GET /v1/catalog | shared | `catalog items=12 rev=3`, 2048 bytes |
| GET /v1/me | per key | `me tenant=T key=K label=L`, 256 bytes |
| GET /v1/items | per tenant | `items tenant=T n=N` (q.n, 1..100, default 5), 120*N bytes |
| POST /v1/items | none | `created tenant=T`, 64 bytes (status 201) |
| GET /v1/blob | per tenant | `blob tenant=T size=S` (q.size, a size up to 1MiB, default 1KiB), S bytes |
| GET /v1/report | none | `report tenant=T attempt=A`, 1500 bytes; with q.fail=F attempts 1..F return 503 `unavailable` (11 bytes) |

Unknown paths return 404 `not found` (9 bytes); bad parameters return 400.
Paths are normalised (repeated slashes collapsed, trailing slash ignored).

## Cache

* Only status-200 GET responses of cacheable routes are stored, for the
  tenant's `cache.ttl` (the default layer's value for shared routes).  An
  entry stored at S with ttl D is served while now < S + D.
* **Isolation.**  A response is only ever served to callers that could
  have received exactly that response from the upstream: shared routes are
  cached once for everybody, per-tenant routes separately for each tenant,
  per-key routes separately for each key of each tenant.  Requests that
  differ only in the order of their `q.` parameters, or in `nonce`/`ts`, are
  the same request.
* A POST to a path removes the tenant's cached responses for that path.
* **Capacity.**  Each entry is accounted at its size rounded up to whole
  KiB; the cache holds at most `cache.capacity` rounded down to whole KiB.
  When a new entry does not fit, the least recently used entries are evicted
  until it does; an entry larger than the whole capacity is not stored.
* A hit is counted, metered and billed exactly like an upstream response
  of the same size.

## Jobs

`job submit` authenticates the credential (refusals are printed like
request refusals) and queues a GET of PATH for the key, due after `delay`
(default 0): `job ID queued due=MS`.  `jobs run` runs every job that is due
(due time <= now), in queue order: earlier due time first, then higher
`prio` (-9..9, default 0), then submission order.  A job put back for a
retry keeps its submission order.  Each run prints one line:

* `job ID done STATUS SIZEB BODY` (status below 500);
* `job ID retry attempt=A next=MS` after the A-th failed attempt (status
  500 or above), next = now + `jobs.backoff` * 2^(A-1);
* `job ID dead attempts=A` when `jobs.max_attempts` attempts have failed;
* `job ID failed REASON` when the key is no longer usable (`auth STATE`)
  or a quota refuses the run (`quota-requests`, `quota-egress`); such jobs
  are not retried.

Jobs are not rate limited and do not use the cache.  A successful run
counts against both quotas and is metered (as a job) like a request; the
quota rules apply to every job of a batch exactly as they would to the
same runs made one command at a time.  Finished jobs of a tenant with a
`webhook.url` produce an outbox entry (`webhook list`).

## Metering and bills

Every accepted request and successful job run is metered for its tenant.
Egress is metered **per response**, each rounded up to whole KiB (a 1-byte
response counts 1 KiB, 1025 bytes count 2 KiB, 0 bytes count 0 KiB).

`bill TENANT` prints

    bill TENANT plan=PLAN
      api N x PRICEmc = AMOUNT
      jobs N x PRICEmc = AMOUNT
      egress NKiB x PRICEmc = AMOUNT
      total AMOUNT

with the tenant's current prices.  Each line is quantity x price in
millicents, rounded half up to whole cents; the total is the sum of the
rounded lines.  `bill` alone prints every tenant's bill, by tenant name.

## Other output

* `usage TENANT` prints the current quota period
  (`usage T period=K requests=N/LIMIT egress=NB/LIMIT`), the rate-limit
  state and the lifetime meter.
* `top` lists tenants by metered requests (most first, ties by name).
* `audit` lines are `#SEQ t=MS TENANT EVENT name=value ...`; values with
  blanks or double quotes are quoted, `"` inside is written `\"`.
  Requests and job submissions record the command line (secrets masked,
  see "Secrets") and the result.
* `audit export` writes TSV (backslash, tab and line breaks escaped as
  `\\`, `\t`, `\n`) or JSON lines.

## Consistency check

After every command, and whenever a request or job has been accepted, the
program checks its own state against the rules above (quotas and rate
limits not exceeded under the current configuration, cache accounting,
queue sanity, meter sanity).  If a check fails it prints
`INVARIANT: DESCRIPTION` on standard error and exits with status 86;
output printed before that point stays printed.
