# Demo Runbook: Bad Deployment Causes Checkout Latency Degradation

This is the canonical IncidentIQ demonstration scenario. It is designed for a
2–4 minute walkthrough of evidence-first incident investigation.

The simulator creates controlled checkout-service telemetry. IncidentIQ then
uses its existing detection, correlation, incident, investigation, and
reasoning workflows. The simulator supplies evidence; it does not decide a
root cause or create an incident itself.

## Prerequisites

From the repository root, start local infrastructure and apply migrations:

```bash
docker compose up -d postgres redis
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
```

Start the API in one terminal:

```bash
backend/.venv/bin/uvicorn backend.app.main:app --reload
```

Start the frontend in another terminal:

```bash
npm run dev
```

The frontend is normally available at `http://localhost:5173`; its checked-in
local configuration points API calls to `http://127.0.0.1:8000`. Confirm the
API before beginning:

```bash
curl http://127.0.0.1:8000/health
```

For AI-backed reasoning, start Ollama and ensure the configured model is
available:

```bash
ollama serve
ollama pull qwen2.5:3b-instruct
```

`AIReasoner` uses `qwen2.5:3b-instruct` at `http://localhost:11434`. If Ollama
is unavailable, the existing investigation route uses its deterministic
fallback. The evidence-backed workflow remains available, but the result shows
its fallback reasoning source.

Before the demo, register or log in with a user account, create a project, and
create at least one service. The simulator uses the first service in the
selected project.

## Canonical scenario

**Bad Deployment Causes Checkout Latency Degradation**

```text
Healthy environment
→ deploy bad version
→ telemetry changes
→ anomaly detected
→ correlated incident created
→ timeline reconstructed
→ historical incidents retrieved
→ AI investigation requested
→ evidence-backed hypothesis shown
→ human reviews result
→ incident can be resolved
→ simulation can be reset
```

Historical retrieval is always attempted as part of investigation context. It
may return no matches until historical incidents have been stored. An
investigation result is a hypothesis, not a guaranteed root cause.

## Evidence created by the simulator

The scenario records only these inputs:

- 20 normal `checkout_latency` observations near 100 ms.
- Five anomalous `checkout_latency` observations: 160, 165, 162, 168, and
  170 ms.
- One current elevated `checkout_latency` observation of 175 ms.
- Deployment `v2.4.0`: “Deployed checkout payment integration changes.”
- One `ERROR` log: “Checkout requests are timing out while calling payment
  service.”

## Evidence versus conclusions

| Simulator-generated evidence | IncidentIQ-generated conclusions and investigation material |
| --- | --- |
| Metric, deployment, and log records listed above | Anomaly detection and severity assessment |
| Timestamps and service association | Correlation of relevant signals and incident formation |
| No causality or root-cause claim | Incident severity, timeline, and linked evidence |
| No generated hypothesis | Historical retrieval and an evidence-backed investigation hypothesis |

IncidentIQ derives conclusions from the supplied evidence using the existing
pipeline. The reviewer should inspect the timeline, supporting evidence,
alternatives, and next steps before resolving an incident.

## Demo walkthrough

1. Open `http://localhost:5173` and log in. Register a new account first if
   needed.
2. Open **Projects**, select the prepared project, and choose **Production
   simulator**.
3. Start from the healthy state. Explain that this creates controlled telemetry;
   it does not modify production infrastructure.
4. Select **Deploy Bad Version**. The simulator records baseline metrics, a
   deployment, elevated metrics, and a payment timeout log, then submits the
   final metric to the existing IncidentIQ incident pipeline.
5. When an incident is detected, select **Open Investigation**.
6. In **Incident timeline**, show the deployment, latency change, and timeout
   event in chronological context.
7. In **Similar incidents**, show historical intelligence. An empty result is
   valid when no qualifying historical record exists.
8. In **Investigation**, select **Create Investigation**, **Start
   Investigation**, then **Generate Investigation**.
9. Review the evidence-backed hypothesis, confidence, alternatives, and next
   steps. Select supporting evidence to inspect its provenance. This is the
   human review point; do not present the hypothesis as a confirmed cause.
10. If demonstrating lifecycle closure, resolve the incident through the
    project incident API (or its corresponding product control when available):

    ```text
    POST /api/projects/{project_id}/incidents/{incident_id}/resolve
    ```

11. Return to **Production simulator** and select **Reset Simulation**. Reset
    removes only simulator-owned telemetry and its simulator-created incident.
12. Select **Deploy Bad Version** again to demonstrate a clean rerun.

## What this demonstrates

- **Evidence-first incident investigation:** conclusions remain tied to
  inspectable telemetry and deployment evidence.
- **Telemetry correlation:** latency degradation, an error log, and deployment
  activity are considered together in time and service context.
- **Explainable anomaly detection:** the incident starts with observable
  baseline and elevated latency signals.
- **Historical retrieval:** prior knowledge can add context without proving
  causality.
- **AI reasoning with provenance:** reasoning includes supporting evidence and
  is validated before persistence; a deterministic fallback is available.
- **Human-in-the-loop investigation:** a reviewer evaluates evidence,
  hypotheses, alternatives, and next steps before acting.

This is a local demonstration scenario. It does not represent real customer
traffic, a commercial SaaS deployment, production reliability measurements, or
a guarantee of root-cause accuracy.

## Troubleshooting

### Backend unavailable

```bash
curl http://127.0.0.1:8000/health
```

If this fails, check `docker compose ps`, start the backend with the command in
[Prerequisites](#prerequisites), and apply migrations if a table is missing.

### Frontend unavailable

Run `npm run dev` at the repository root and open the Vite address printed in
the terminal. Confirm `frontend/.env` points `VITE_API_BASE_URL` at the backend
you started.

### Ollama unavailable

Run `ollama serve` and `ollama pull qwen2.5:3b-instruct`. The investigation
route uses its deterministic fallback if the AI request cannot complete; check
the displayed reasoning source before describing the result.

### Simulation already active

One active simulation is allowed per project. Return to **Production
simulator**, select **Reset Simulation**, and run the scenario again.

### Reset failure

Inspect the backend terminal for the server traceback. Ensure migrations are at
head and the server was started from this repository with `--reload` (or
restart it). A browser CORS message accompanying reset failure can be the
client-side symptom of a backend 500; resolve the backend exception rather than
loosening CORS policy.

### Authentication failure

Log out and sign in again, or register a new user. API requests require the
browser's current bearer token, and access is restricted to projects owned by
that user.
