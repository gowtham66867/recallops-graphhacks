# Verification record

Updated October 18, 2026, using Python 3.12.12, Node 24.18.0, and FalkorDB v4.16.3 on local Docker Desktop.

## Automated checks

- **46 tests passed** against real FalkorDB, plus a mocked Responses API adapter contract test within that suite.
- Production React/TypeScript build passed.
- Five scenario evaluation cases selected the expected supported action or abstained when evidence was insufficient.
- All returned decision evidence IDs resolved to actual graph records.
- Four actionable evaluation cases executed successfully, recalled their outcome through a fresh client, resisted duplicate execution, and reused conditional memory after an explicit replay.
- A fresh Python interpreter recalled the recorded lesson without in-memory application state.
- Four concurrent requests for the same approved attempt produced one outcome/lesson and one state revision increment.
- State changes before approval and after approval invalidated execution.
- Missing FalkorDB produced a visible 503, with no dataset fallback.
- Failed historical restart and incompatible rollback were rejected; unknown schema did not establish compatibility.
- The simulator did not recover a connection-exhaustion fault when a feature flag was disabled directly in the rule test.
- A newly recorded successful lesson stopped qualifying for reuse when the schema changed.

Measured case data and local timings: [evaluation.json](evaluation.json). These timings include evidence validation reads and exclude model latency. This small synthetic suite does not establish general operational accuracy.

## Persistence across a database restart

Created a separate `durability_check_checkout` graph, executed and recorded one approved simulator action, restarted the FalkorDB container, and reconnected from a new Python process. The lesson count remained one and recovered error rate remained 0.2%. The disposable graph was removed after verification. The user's app graph was not reset by this check.

## Browser checks

Inspected the actual app at a desktop viewport and a 390px iframe viewport.

Desktop interactions verified:
1. Selected rejected rollback and observed schema-v2-versus-v3 explanation.
2. Opened its original manifest source record.
3. Reviewed the specific proposed action and state revision in the approval dialog.
4. Approved and ran the simulation; observed 18.4% → 0.2% recovery.
5. Opened a fresh session; observed a new session ID and one recalled lesson.
6. Replayed the incident without erasing experience; observed the recommendation citing the matching prior success and a new source chip.

Narrow layout inspection verified top navigation, scenario selector, stacked layout, incident summary and metric cards at 390px. Graph inspection has keyboard-accessible node buttons and textual source/decision alternatives. Modal focus is trapped and Escape dismisses a non-busy dialog. This is not a full accessibility audit.

## Limits and remaining work

- A real provider request was attempted and returned HTTP 429 `credit_balance_exhausted`. No successful live investigation or same-model historical-context comparison has been recorded. The mocked adapter contract test is not a live model evaluation.
- One dependency deprecation warning from Starlette's test client/AnyIO was emitted; it did not fail tests.
- A password-protected Google Cloud deployment passed external HTTPS and workflow checks; see DEPLOYMENT.md. The source repository and build-story article are public, and the narrated demo video has been rendered. YouTube publication and hackathon submission are pending; this record does not claim they have completed.
- The hosted demo uses shared access credentials. It has no per-user authorization, tenant isolation, external telemetry, or real remediation integration.


## Architecture upgrade verification — October 18

- Five checkpointed workflow scenarios passed against real FalkorDB.
- Two context ablations changed rule decisions when graph history was removed. See architecture-evaluation.json.
- Resume reused completed specialist stages after a simulated interrupted reasoning stage. A changed fact digest blocked resume; completed resume was idempotent.
- Public proposal requests without a verified run were rejected. Schema and original-source changes invalidated handoff/approval even without a revision increment.
- Missing sources and invalid citations blocked review. An independent critic's rejection blocked the recommendation in a mocked provider contract test.
- Typed live-assessment contract tests verified model abstention and correction of an unsupported action within the call budget. These tests mock the API and do not establish actual model performance.
- Counterfactual forecasts did not mutate facts or create observed lessons.

The original 23-test and browser records above describe the initial build. The expanded suite is 46 tests. Live provider validation remains outstanding.

The upgraded browser flow also completed a compatible rollback through a verified run, human approval and simulation, changing the deployed version to v2.7.0 and recording recovery. A new provenance test verifies that changed operational state is linked to its new simulator observation source.

Recovery was also verified in the browser: a separate Python process deliberately interrupted a demonstration after the collected-evidence checkpoint, without changing domain state. The Saved investigations panel discovered it, Resume completed the remaining stages through the API worker, and the audit showed a completed run with one resume. This was a simulated stage interruption; it was not a live-model crash or per-tool cold-resume experiment.

## Interactive context experiment

The System map runs history ablation on a disposable copy of the current factual graph. Two additional real-database tests verify changed decisions, unchanged source digests, and removal of temporary graphs. The full suite now contains 46 tests.

## Publication and hosted experiment checks

The public repository's GitHub Actions pipeline passed on a fresh Linux runner:
46 tests, five architecture cases, two context ablations, and the production
frontend build. The hosted HTTPS workflow passed after the ablation upgrade.
The hosted context experiment changed restart from contradicted to unknown;
the source snapshot before and after the experiment was identical.

The prepared recorded walkthrough uses actual UI captures and synthetic
narration. It explicitly discloses deterministic mode and the unverified optional
live-model path. See DEMO.md for its exact chaptered transcript.
