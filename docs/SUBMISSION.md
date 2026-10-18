# Submission record

## Name
RecallOps — Incident memory that knows when a fix expires

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

## Prepared submission assets

- Public source: https://github.com/gowtham66867/recallops-graphhacks
- Recorded demo and captions: https://github.com/gowtham66867/recallops-graphhacks/releases/tag/v1.0.0
- Hosted app: https://34.46.171.202.sslip.io (password protected)
- Build story: https://github.com/gowtham66867/recallops-graphhacks/blob/main/docs/BLOG.md
- Graph schema: README.md and docs/ARCHITECTURE.md
- Exact graph queries: docs/GRAPH_QUERIES.cypher
- Reproducible verification: 60 tests, five scenario cases, two history ablations; CI passed.
- Tracks: Agent Memory and Coordination; Agents That Act on Connected Data.

## Submitted

The signed-in WeMakeDevs portal confirmed **Submitted** for
**GraphHacksChampions** (team code `975BKB`), filed October 18, 2026, at
**5:36 PM IST**. Both selected tracks are recorded:

- Agents That Act on Connected Data
- Agent Memory and Coordination

The submission includes the public repository, graph schema and exact Cypher
queries, the build-story article, the protected live deployment, and the
approved demo-only login for judges. The login is not published in this source
repository.

YouTube demo: https://youtu.be/UNLjAmICQVE — **Unlisted**, with English captions.
It uses actual UI captures and synthetic narration. YouTube's upload checks
reported no issues. The local confirmation screenshot and metadata are saved in
ignored `artifacts/` files.

The available OpenAI project still returns `credit_balance_exhausted`. The entry
explicitly discloses deterministic mode and does not claim a verified live model.
AI coding and writing assistance are disclosed in the submitted description.

The portal says the team may edit until the deadline: October 18, 2026,
11:59 PM IST. The signed-in submission page is
https://www.wemakedevs.org/hackathons/falkordb/submit .


## Verified upgrade before the deadline

On October 18 at **6:30 PM IST**, the portal again showed **Submitted** after
saving the Proof Lab description and updated 60-test verification count. Both
tracks, the original captioned YouTube demo, judge login, and repository links
were retained. The entry now links judges to the interactive lab and its
walkthrough. No withdrawal or new submission was needed.

Release: https://github.com/gowtham66867/recallops-graphhacks/releases/tag/v1.1.0

External HTTPS checks verified observed recovery, conditional memory reuse,
HTTP 409 on stale approved context, retained but ineligible lessons after schema
drift, and preservation of the main scenario. See proof-lab-verification.json.


## Final feedback adaptation — confirmed before closing

At **11:51 PM IST on October 18**, the signed-in portal again confirmed
**Submitted**, with the responder-context upgrade and **95 passing tests**
(87 Python, 8 frontend). The original video, both tracks, repository, deployed URL
and approved demo login were retained. The captioned core video predates this
upgrade; the entry explicitly discloses that and the unconfigured/live-unverified
Gemini audio path. Source, UI evidence and limits are in FEEDBACK_IMPLEMENTATION.md.

The deployed build passed external HTTPS checks for audience-specific approved
exports and audio consent, and the Proof Lab recovery/race smoke test passed.
The main checkout scenario was preserved. The implementation commit's GitHub CI
passed all Python/frontend tests, architecture evaluation, and production build.
