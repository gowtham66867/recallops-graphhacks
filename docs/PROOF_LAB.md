# Two-minute judge challenge

Open the protected [live Proof Lab](https://34.46.171.202.sslip.io/?view=lab).
The demo login is in the hackathon entry. No model key is needed.

## 1. See real recovery and persistent memory

Select **Feature regression**, then **1. Investigate**, **2. Propose remedy**,
**3. Approve simulation**, and **5. Attempt execution**. Skip drift for this run.
Errors recover from 18.4% to 0.2%. A new observed lesson appears below.
Its conditions match, but further action is gated because the incident is resolved.

Select **Feature regression** again. This reintroduces the fault while preserving
experience. The prior lesson now reads **Eligible now** and supplements the
recommendation's evidence. Configuration does not manufacture a successful outcome.

## 2. Break an approval

Investigate, propose, and approve the new remedy. Select **4. Inject schema drift**,
then **5. Attempt execution**. This calls the same executor as Incident command.
The real API returns HTTP 409. The proposal becomes invalidated and error rate
stays at 18.4%. The proof panel compares the approved and current revisions and
SHA-256 evidence fingerprints. The client displays success only after a 409,
a retrieved invalidated proposal, and an unchanged incident error rate.

The saved lesson remains visible but now reads **Conditions changed**:
recorded schema v3 versus current schema v4. Memory is retained; authority to
reuse it expires. Reapplying the original conditions restores eligibility.

## 3. Explore alternate faults

**Safe rollback** selects a matching schema-v2 release regression, supported by
recorded prior recovery. **Pool exhaustion** supports increasing capacity.
**Unknown cause** leaves the system without a supported remedy. Change inputs
and inspect their effects; the observation classification is a user input,
not a live model diagnosis.

## Architecture and limits

- A UUID stored in browser local storage selects a distinct FalkorDB graph under
  the configured graph prefix. The five main scenario graphs remain untouched.
- Configuration and current telemetry are updated atomically under the same
  mutation lock used by approval and execution. Historical outcome sources stay intact.
- A fresh verified workflow is required before proposing a remedy. Configuration
  drift invalidates both workflow handoff and previously approved action context.
- The lesson inspector separates signature/schema/outcome matching from current
  policy eligibility. Matching a lesson does not override resolved state or
  unsupported action preconditions.
- The demo has shared authentication, no per-user authorization or graph ownership
  checks. UUID scoping is convenience separation, not a security boundary.
- Reset removes this lab's synthetic records only. Lab graphs persist until reset
  or administrative cleanup; no background retention policy is implemented.
- All remediation is deterministic simulation. No production service is contacted.

Verification: 60 tests across the whole project, using real FalkorDB and
explicitly mocked provider contracts, including 14 Proof Lab cases, plus TypeScript production build and five architecture scenarios
with two graph-context ablations. Live provider validation remains outstanding.
