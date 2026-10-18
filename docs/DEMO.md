# Recorded demo walkthrough

Published as Unlisted: https://youtu.be/UNLjAmICQVE (English captions included).

The prepared video is 4 minutes 7 seconds, 1920×1080 H.264 with AAC audio.
It is an edited walkthrough of actual browser interactions, narrated with
synthetic speech. It demonstrates deterministic investigation; it does not
represent a successful live-model run. All domain data and remediation effects
are synthetic.

The source captures show evidence inspection, a real approved simulator
transition, cross-session memory, replay, graph-context ablation, and abstention.
The video includes these scope disclosures in its narration.

## 0:00 — The problem

Yesterday's successful fix can be today's wrong answer. RecallOps is an incident command center that remembers the conditions behind an outcome. Here, a synthetic checkout service is failing after a deployment. Every incident and metric in this walkthrough is fictional. The database, evidence queries, and persistence are real.

## 0:19 — Remember failed fixes

The obvious restart is rejected. FalkorDB connects today's affected service to incident seventeen, its attempted restart, the failed outcome, and its original postmortem. The same failure signature is present. A remembered failure becomes evidence against repeating an ineffective action.

## 0:37 — Historical success is conditional

Rollback worked in incident twenty one. But it worked with schema version two. The current deployment uses schema version three. RecallOps checks those paths together and rejects the incompatible rollback. A successful memory is not permanent permission.

## 0:52 — Inspect original evidence

Every decision opens its supporting source. This manifest states the current schema, the previous application's requirements, and the stable checkout path's compatibility. The explanation is traceable to an original graph record, rather than an unsupported confidence score.

## 1:09 — Verify before acting

The workflow plans, collects, reasons, reviews, and completes. Three deterministic specialists collect configuration, topology, and memory concurrently. Six bounded tools inspect the graph and compare alternatives. Forecasts are labeled predictions. Five durable checkpoints and an evidence digest bind the completed investigation to its proposed action.

## 1:32 — Keep execution authority separate

The supported feature flag change still needs human approval. This proposal names the command, preconditions, and state revision. Before execution, the system checks the evidence hash again. Changed source text or deployment conditions invalidate the handoff. The investigator has no execution authority.

## 1:51 — Record an observed outcome

After approval, the simulator applies its documented transition. The synthetic error rate falls from eighteen point four to zero point two percent. The action attempt, observed outcome, original observation source, and conditional lesson are written together in one graph query. Repeated execution returns the same recorded result.

## 2:11 — Recall across sessions

Now open a fresh session. The lesson is retrieved from FalkorDB, with its failure signature, schema, and source. It survives the conversation because the outcome lives in the graph. The application explicitly reminds the next responder to revalidate its conditions before reuse.

## 2:28 — Reuse conditions, not slogans

Replay deliberately reintroduces the synthetic fault while preserving experience. The new investigation incorporates the recorded success only after checking that the current signature and schema still match. This is conditional memory reuse, not model training or a claim of autonomous learning.

## 2:45 — Remove the context

To test whether the graph changes behavior, run the context experiment. It copies the current facts into a disposable FalkorDB graph and removes historical connections. With history, restart is contradicted. Without those edges, it becomes unknown. The original graph is preserved.

## 3:03 — A second controlled comparison

The compatible rollback scenario provides a second comparison. With matching historical recovery, rollback is supported. Remove that history, and the same policy returns unknown. Current deployment evidence stays intact. These are deterministic context ablations, not language model accuracy benchmarks.

## 3:22 — Abstain when evidence is missing

When the current schema is unverified, RecallOps abstains and disables action review. Missing evidence does not become safety. Forty six tests cover the real database, stale evidence, duplicate execution, checkpoint recovery, and graph isolation during the experiment.

## 3:40 — Scope and reproducibility

This recording uses deterministic investigation. The optional live tool calling investigator and independent model critic are implemented, but successful provider execution remains unverified because the available API project has exhausted its credits. Source code, setup instructions, Cypher queries, architecture, and measured evaluations are public. RecallOps remembers what worked, why it worked, and when it no longer applies.
