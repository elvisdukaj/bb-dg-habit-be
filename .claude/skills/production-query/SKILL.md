---
name: production-query
description: >
  Use before implementing any change to a live, instrumented service. Gathers production
  baselines, dependency maps, and SLO health via `bluebox ask` before design or code begins.
  Triggers: "what does production look like", "current error rate", "p95/p99 latency",
  "upstream callers", "downstream dependencies", "can it handle the load", "production baseline",
  "is there an active problem", "what SLOs are at risk", "bluebox ask".
compatibility: Coding agents (Claude Code, Cursor, Windsurf, Copilot, Kiro, OpenCode)
allowed-tools:
  - Bash
  - Read
metadata:
  version: "0.5.0"
  audience: coding-agent
---

# Production Query

## Scope

Before you design or implement anything that touches a live service (a new endpoint, a
dependency change, a performance-sensitive path, a data migration), gather production context
first. Don't guess at current behavior; ask production.

## Change risk tier

The tier determines query depth.

| Tier | Impact | Examples | Query depth |
|------|-------|----------|-------------|
| **0 — Minimal** | No production impact; docs, internal tooling | README update, dev script | Skip — no production query needed |
| **1 — Standard** | Single service, existing patterns, low blast radius | Bug fix, config change, dependency update | Baseline + dependencies |
| **2 — Full** | Multi-service, new patterns, high blast radius | New API endpoint, schema migration, cross-service change | Full planning workflow |

If in doubt, treat the change as Tier 1.

## Command

Syntax: `bluebox ask [flags] "<question>"`. Flags must come before the question string.

| Flag | Meaning |
|---|---|
| `--service <name>` | OTel `service.name` — pass it when discoverable from the project |
| `--env <name>` | Deployment environment (`deployment.environment`), if known from project/deploy config |
| `--conversation-id <uuid>` | Continue a previous run (from the `conversation:` line on stdout) |

* **stdout** = the answer (markdown) plus a final `conversation: <uuid>` line (printed even on
  failure). **stderr** = progress/tool activity and, on failure, the error reason. Parse the
  answer from stdout only; read stderr only to diagnose failures.
* The query agent is **read-only** — no mutations result from a query.
* **Runtime:** answers typically take 1–2 minutes (the server caps one ask at ~90s of agent
  time). Set your command timeout to ≥5 minutes (300000 ms).
* If ANSI escape codes appear in the output, prefix the command with `NO_COLOR=1`. Don't
  append `| cat` — it hides the exit code.
* Exit `0` = the agent completed; non-zero = failure, timeout, or cancellation. **Treat
  non-zero as a blocker** — read stderr, resolve, retry; don't fabricate an answer.
* **Exit `0` with a `## Cannot complete` section is a non-answer** — the agent lacked context.
  Refine the question or supply `--service`/`--env`, then retry. Don't treat it as evidence.

## Service name

`--service` maps to the OTel `service.name` resource attribute, set in the app's SDK/agent
config. Check the project before asking:

| Runtime | Where `service.name` is typically set |
|---|---|
| Go | `resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName("<name>"))`, or `OTEL_SERVICE_NAME` |
| Python | `Resource.create({"service.name": "<name>"})`, or `OTEL_SERVICE_NAME` |
| Node.js | `new Resource({ [ATTR_SERVICE_NAME]: "<name>" })` (`@opentelemetry/resources`), or `OTEL_SERVICE_NAME` |
| Java / Spring Boot | `OTEL_SERVICE_NAME`, `-Dotel.service.name=<name>`, or `otel.service.name` in agent/`application.properties` |
| Any / Kubernetes | Pod spec `OTEL_RESOURCE_ATTRIBUTES=service.name=<name>`, or OTel Operator annotations |
| Collector config | Resource processor: `service.name: <value>` |

If the project used the Bluebox **instrumentation** skill, the generated config file contains
the service name. `--env` comes from the same places (`deployment.environment`); omit it if
unknown.

### Discovery commands

Run these in order; stop at the first conclusive match. **Never pass a guessed name to
`--service`**; a wrong name returns empty or misleading data.

**Kubernetes / Helm:**

```bash
grep -r 'app\.kubernetes\.io/name\|app:' k8s/ deploy/ manifests/ .k8s/ 2>/dev/null | grep -v '#'
grep -r 'nameOverride\|service\.name\|^name:' charts/ helm/ */Chart.yaml */values.yaml 2>/dev/null
```

**OTel config / env vars:**

```bash
grep -r 'service\.name' --include='*.yaml' --include='*.yml' . 2>/dev/null | grep -v node_modules
grep -r 'OTEL_SERVICE_NAME\|OTEL_RESOURCE_ATTRIBUTES' .env* docker-compose*.yml Dockerfile* k8s/ 2>/dev/null
```

**Language manifests:**

```bash
grep '"name"' package.json 2>/dev/null | head -1            # Node.js
grep -m1 '^module ' go.mod 2>/dev/null                      # Go (last path segment)
grep 'spring\.application\.name\|otel\.service\.name' \
  src/main/resources/*.properties src/main/resources/*.yml 2>/dev/null  # Java/Spring
grep -m1 '^name\s*=' setup.cfg pyproject.toml 2>/dev/null   # Python
grep '<AssemblyName>' *.csproj 2>/dev/null                  # .NET
```

If none of the above yields a confident match, ask the user directly.

## Planning workflow

Work outside-in; each step is one `bluebox ask`, chained with `--conversation-id` so the
agent keeps context:

1. **Baseline** — "current request rate, error rate, and p50/p95/p99 latency for `<service>`
   in `<env>` over the last 24h?"
2. **Dependencies** — "what does `<service>` call, and what calls `<service>` — at what rate?"
3. **Capacity / SLO** — "what's `<service>`'s CPU/memory headroom right now, what SLOs are
   defined, and are any at risk?"
4. **Drill in** — follow the thread on whatever your change touches (an endpoint, a dependency,
   an error class), reusing the conversation id. Spans tell you *what* failed; logs tell you
   *why*. Ask for the log error message from the failure window before concluding, as span
   status alone often carries no exception detail.
5. **Verdict** — close with an explicit `## Verdict`: **go / no-go / go-with-changes**, the
   evidence behind it, and what (if anything) changes in the implementation plan. Don't stop
   at reporting numbers; the user asked so they could decide.

Combine topics in one question to get correlated reasoning; asking about SLOs and a proposed
traffic increase together, for example, lets the agent reason about breach risk.

**Pick the time window deliberately** (and say which you used):

* Baseline / capacity / trend → **last 24h** (captures the daily cycle).
* Pre-deploy gate / "is it healthy *now*" → **last 30–60 min**.
* Before/after a deploy or incident → a window bracketing that event.

**Mind small samples.** On narrow windows with low traffic, report counts alongside
percentages ("2 of 3 charges failed" is not "100% down"). Don't promote attribute correlations
into mechanisms: "all failures carry `tier=gold`" is an observation; "only gold users are
affected" is an inference.

**Re-verify blockers.** If you reported a blocker and it's now said to be resolved, re-run
the same question (using the same conversation id) before proceeding. Anchor the time window
to the reported resolution time ("clean since <time>?"), not a relative window; right after
recovery, "last 30 min" still contains the incident.

## Query catalog

* **Error rate:** `bluebox ask --service <s> --env <e> "error rate over the last 24h and the top error types"`
* **Latency:** `bluebox ask --service <s> --env <e> "p50/p95/p99 response time over the last 24h, by endpoint"`
* **Upstream callers:** `bluebox ask --service <s> "which services call <s>, and at what rate?"`
* **Downstream deps:** `bluebox ask --service <s> "what does <s> depend on, and which dependency is slowest?"`
* **SLOs:** `bluebox ask --service <s> "what SLOs are defined for <s> and are any currently at risk?"`
* **Capacity / change impact:** `bluebox ask --service <s> "can <s> handle a 30% traffic increase without breaching its SLOs?"`
* **Deploys:** `bluebox ask --service <s> --env <e> "when was <s> last deployed, and did error rate or latency change after it?"`
* **Active problems:** `bluebox ask --service <s> "are there any active problems or anomalies for <s> right now?"`

## Output

* The default answer is a 1–2 sentence summary, an `## Evidence` section, and a
  `## Recommended action` section (omitted when no action is needed). To change the shape,
  ask for it in the question (e.g., "respond with a risk table" or "answer in one sentence");
  requested formats take precedence.
* After each run, capture the `conversation: <uuid>` line and pass `--conversation-id` to keep
  context across questions.

## Boundaries

This is for querying production through Bluebox. Don't bypass to `dtctl` or the Dynatrace
UI; `bluebox ask` is the supported path and keeps the evidence trail visible to Bluebox.

## Prerequisites

* `bluebox auth login` completed, or `BLUEBOX_TOKEN` set for one-shot use.
* Bluebox connected to a Dynatrace environment that receives the service's telemetry.
* Only if the `bluebox` command is **not found**: the CLI installs to `~/.bluebox/bin` —
  `export PATH="$HOME/.bluebox/bin:$PATH"`. If `bluebox` already resolves, use it as-is.
