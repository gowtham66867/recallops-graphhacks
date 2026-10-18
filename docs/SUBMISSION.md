# Submission draft

## Name
RecallOps — incident response with conditional memory

## One-line pitch
An incident agent that remembers failed fixes, rechecks yesterday’s successful fix against today’s system, and carries observed outcomes into the next session.

## Problem
Operational history is full of advice whose assumptions expired. A rollback that worked before a migration may be incompatible today. A repeated restart may reproduce a failure instead of resolving it. Session-local chat loses both the failed attempts and the conditions behind successful ones.

## What we built
A deployed incident command center with a durable plan–collect–reason–review workflow backed by FalkorDB. Three deterministic specialists collect context concurrently; optional live mode adds a tool-calling investigator with typed action selection and an independent model critic. It traverses deployment conditions, dependencies, prior incidents, action attempts, observed outcomes, and original sources. Deterministic applicability checks distinguish supported, contradicted, and unknown actions. Candidate actions are compared through non-mutating simulator forecasts. A verified investigation and its factual context hash are required for handoff. A user reviews a specific proposal before the simulator acts. The observed outcome and conditional lesson are written atomically and recalled across a fresh process or session.

The defining demo rejects a previously unsuccessful restart, invalidates a historically successful rollback after a schema change, and approves a compatible feature-flag action. A replay preserves the lesson while reintroducing the fault, showing how the recommendation incorporates newly observed experience.

## FalkorDB contribution
FalkorDB is the primary context and persistence layer. Native relationships connect current incident → affected service ← historical incident → attempt → outcome → source. Deployment → migration paths supply compatibility evidence. Lesson → outcome and lesson → service paths preserve conditional experience. If FalkorDB is unavailable, investigation fails visibly; no hidden data copy supplies answers.

## Track alignment
Primary: Agent Memory and Coordination — persistent outcome memory, conditional reuse, and cross-session recall.
Secondary: Agents That Act on Connected Data — multi-hop evidence retrieval, graph-dependent decisions, and an approved simulated action.

## Implementation and honesty
Python/FastAPI, official FalkorDB client, React/TypeScript/Vite, Docker Compose. Optional OpenAI Responses tool-calling investigation. The hosted demo runs in deterministic investigation mode. A real provider request returned HTTP 429 `credit_balance_exhausted`; successful live investigator and critic execution remains unverified. All organizations, incidents, telemetry, and remediation effects are synthetic. No production integration or general incident-resolution accuracy is claimed.

## Validation
See docs/VERIFICATION.md and docs/evaluation.json for measured results. Do not replace these with invented performance claims.

## AI assistance
AI coding assistance was used for design, implementation, testing, and documentation. The human submitter must review the code, rerun the demo, and be prepared to explain the schema, rules, and limitations.

## To complete before submission
- Review official signed-in submission form fields and current event rules.
- Configure and test live model access if claiming a live AI demo.
- Create the public source repository and supply its URL.
- Record and upload the working demo; add its URL.
- Deployment complete: https://34.46.171.202.sslip.io (password-protected HTTPS). Provide judges with access through the submission channel; do not publish the password in source code.
- Review all claims against the final implementation and measured results.
- Submit through the event panel before the verified deadline.

Deployment verification is recorded in docs/DEPLOYMENT.md. No public repository or recorded video URL is available in this workspace. This draft has not been submitted.
