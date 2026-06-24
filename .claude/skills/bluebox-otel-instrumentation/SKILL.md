---
name: bluebox-otel-instrumentation
description: >
  Use when asked to instrument a service with OpenTelemetry for Bluebox, or when you find a
  `.env.otel.bluebox-template` file in the repo. Adds the OTel SDK, wires init code adapted to
  the framework, completes the Bluebox config template, and verifies telemetry becomes
  available in Bluebox.
  Triggers: "add OpenTelemetry", "instrument this service", "set up tracing", "OTel setup",
  ".env.otel.bluebox-template", "wire up telemetry for Bluebox".
compatibility: Coding agents (Claude Code, Cursor, Windsurf, Copilot, Kiro, OpenCode, Codex)
metadata:
  version: "0.3.0"
  audience: coding-agent
---

# Bluebox OTel Instrumentation

## Scope

Instrument the services in this repository with OpenTelemetry so their traces/metrics/logs
become available in Bluebox. You inspect the repo, add the SDK, wire init code to the
framework, complete the config template, and verify data flows. You adapt to the repo — this
skill is reference and rules, not a fixed recipe.

## Hard rules (read first)

1. **Never handle the ingest token.** Do not fetch it, print it, paste it into a file, or pass
   it as a CLI argument. The token is the user's to place in their secret store. You wire the
   app to *read* it from an env var; the user supplies the value.
2. **Config comes from the environment.** No endpoints, tokens, or secrets hardcoded in source.
3. **Never commit a secret.** If you create or edit a file that will hold a real token in the
   user's environment, confirm it is git-ignored first.
4. **Explain every change** you make to the user's code, and why.
5. The static transport values are **fixed**: `http/protobuf` over the HTTP OTLP endpoint,
   header `Authorization=Api-Token <token>`. Do not switch to gRPC or port 4317.

## Start from the template

Bluebox `setup` drops **`.env.otel.bluebox-template`** at the repo root. It is the canonical
config contract — complete it, don't invent a parallel one. It already contains the static
values and documents (as comments) the token header form. Two things are intentionally blank:

- `OTEL_EXPORTER_OTLP_ENDPOINT` — you fetch this (below).
- `OTEL_SERVICE_NAME` / `OTEL_RESOURCE_ATTRIBUTES` — you set these per service.

The token line is a **comment only** and stays that way. Copy the file to wherever the app
actually loads env (e.g. a git-ignored `.env.otel`), keeping the same variable names.

**If the template isn't present**, regenerate it rather than hand-writing one — that keeps the
static values authoritative:

```bash
bluebox setup instrumentation   # agent mode is the default; rewrites the template
```

## Workflow

1. **Detect** language, framework, and deployment model from the repo (manifests, lockfiles,
   Dockerfile/compose, `k8s/`). Adapt — don't assume.
2. **Add the SDK + init** using the per-language reference below. Prefer zero-code / auto-
   instrumentation entrypoints; only add code where the framework needs an explicit hook.
3. **Fetch the endpoint** and write it into the config:

   The template may already have `OTEL_EXPORTER_OTLP_ENDPOINT` pre-filled — if so, use it.

   If the field is blank, run:
   ```bash
   bluebox otlp-endpoint   # prints only the bare endpoint URL to stdout — never the token
   ```
   On success (exit 0) the endpoint URL is on stdout; write it into the template.

   **Exit 1** means the endpoint is not yet available — the workspace is still provisioning.
   Wait and retry (e.g. every 30 s for a few minutes). This is decoupled from onboarding
   on purpose.

   **Exit 2** is terminal — the workspace requires manual connection setup and will never
   auto-provision an endpoint. Do not retry. Tell the user to open the Bluebox web UI and
   configure their monitoring environment connection before proceeding.
4. **Set the service identity** — `OTEL_SERVICE_NAME` per service, plus
   `OTEL_RESOURCE_ATTRIBUTES=service.namespace=...,deployment.environment=...`.
5. **The token — hand off to the user.** Tell the user:
   - **Where to get it:** Open Bluebox → Onboarding → Instrumentation setup → **Reveal token**.
   - **Where to put it:** Describe the exact mechanism you actually wired — the specific env var,
     secret key, or config field you set up for this app. Do not name a generic variable; name
     the real one. Do not claim you wired a specific variable unless you actually did.
   - **How to handle it:** It belongs in their secret store or a git-ignored local env file and
     must never be committed.

   You never see or store the value.
6. **Wire deployment** — show the env injection for their model (Dockerfile `ENV`/`--env-file`,
   compose `environment:`, k8s `envFrom`/Secret) as instructions or a template. Reference the
   token via a secret, never inline.
7. **Verify** telemetry flows (below). Don't declare success until you've seen data or a clean
   exporter handshake.

## Secret handling

| Environment | Where the token goes | What you do |
|---|---|---|
| Local dev | git-ignored `.env.otel` or shell `export` | Wire app to read env; tell user to fill it; confirm `.gitignore` covers it |
| Production | Kubernetes Secret / cloud secret manager / the user's equivalent | Reference the secret in the deployment; **do not** build or assume a specific secret backend |

Never print the token, never write it to a tracked file, never echo it in a command you run.

## Per-language reference

Compact starting points — adapt to the detected framework. Prefer the auto-instrumentation
path; it's less code and less to maintain.

| Lang | Add | Init / entrypoint | Framework hooks |
|---|---|---|---|
| Go | `go.opentelemetry.io/otel`, `otel/sdk`, OTLP HTTP exporter, contrib instrumentation | `otel.go`: resource + tracer provider + OTLP/HTTP exporter | `otelgin`, `otelecho`, `otelhttp`, `otelgrpc` middleware |
| Node/TS | `@opentelemetry/sdk-node`, `auto-instrumentations-node`, OTLP HTTP exporter | `--require ./instrumentation.mjs` (NodeSDK) | auto-instrumentations cover Express/Fastify/Nest |
| Python | `opentelemetry-distro`, `opentelemetry-exporter-otlp-proto-http`; `opentelemetry-bootstrap -a install` | `opentelemetry-instrument <app cmd>` (zero-code) | distro auto-instruments Flask/FastAPI/Django |
| Java | OTel Java agent JAR | `-javaagent:opentelemetry-javaagent.jar` (zero-code) | agent auto-detects Spring/Quarkus/etc. |
| Ruby | `opentelemetry-sdk`, `opentelemetry-instrumentation-all`, OTLP exporter | initializer: `OpenTelemetry::SDK.configure { |c| c.use_all }` | `use_all` covers Rails/Sinatra |
| Rust | `opentelemetry`, `opentelemetry-otlp`, `tracing-opentelemetry` | init tracer provider + `tracing` subscriber bridge | per-framework `tower`/middleware layer |

All read transport config from the `OTEL_*` env vars in the template — no per-language endpoint
or token literals.

## Verify

Once the user has placed the token and the app is running with some traffic, ask Bluebox
directly whether telemetry has arrived — this confirms the full path (SDK → OTLP endpoint →
Bluebox):

```bash
bluebox ask --service <OTEL_SERVICE_NAME> "are any spans or traces arriving for <service> in the last 15 minutes?"
```

`bluebox ask` is read-only and queries live data; a positive answer means the entire pipeline
is working. Allow a few minutes after first traffic before concluding no data is flowing. For
deeper query patterns, time-window guidance, and `--env` usage, load the **`production-query`**
skill.

**Secondary checks (if `bluebox ask` is not yet available or returns no data):**
- Point the exporter at a local collector with a debug/logging exporter to confirm the SDK is
  emitting, then switch back to the real endpoint.
- A 401/403 on export means the token isn't reaching the runtime from the secret store — a
  user/secret-store issue, not a code issue. Surface it; don't try to fix it by embedding a token.

## Boundaries

- You own code and config changes. You do **not** own the token or the user's secret store.
- Don't bypass the template's variable contract or hardcode transport values.
- Don't build a secret-management workflow — reference the user's existing store.

## Prerequisites

- `bluebox setup` has run (so the template and this skill are present).
- The Bluebox workspace is connected to an observability backend (for the endpoint to resolve).
