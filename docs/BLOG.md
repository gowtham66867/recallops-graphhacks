# Yesterday’s successful fix can be today’s wrong answer

An incident agent remembers that a rollback worked. Then a schema migration lands. The next outage looks familiar, so the agent recommends the same rollback. The memory is accurate; the advice is outdated.

That is the problem behind RecallOps. The goal was an incident assistant that preserves the conditions behind an outcome, not just a sentence saying “rollback fixed checkout.”

The prototype uses a fictional commerce system. FalkorDB connects current incidents to services, deployments, migrations, historical attempts, observed outcomes, and original source records. The investigation can follow the path from today’s checkout incident through the service to an earlier attempt and its result. A separate deployment-to-migration path describes the system as it is now.

The useful comparison happens where those paths meet. Did the historical action assume schema v2? Is the current schema v3? A deterministic compatibility check can reject that action even when a retrieved postmortem sounds persuasive. Missing telemetry remains unknown rather than becoming permission.

The demonstration also records a failed restart. Remembering failure is useful because an agent can otherwise repeat an attractive but ineffective action. RecallOps ties that failure to its observed signature; it does not ban every future restart because one once failed.

A user reviews the supported action before execution. Everything runs in a clearly labeled local simulator. The simulator applies explicit transition rules and generates observations. An endpoint returning successfully is not the recovery criterion: the observed error rate must fall below the configured threshold.

The resulting attempt, outcome, source, and conditional lesson are committed together in one FalkorDB query. A new application session reads that durable graph. A replay control explicitly reintroduces the fictional fault while retaining experience, making it possible to inspect how the newly recorded outcome supplements the next recommendation.

The model’s role is deliberately bounded. An optional Responses API agent can investigate through read-only tools and explain the evidence. Deterministic checks govern action applicability, and the model cannot approve execution. Without a configured API key, the application labels its investigation as deterministic. A real provider attempt returned `credit_balance_exhausted`; successful live model execution remains unverified. The recorded demo uses deterministic investigation.

The evaluation is intentionally modest: predefined synthetic scenarios, real FalkorDB integration tests, and measured results kept in the repository. It establishes specific implementation behaviors, not production incident accuracy or superiority to every other database architecture.

The lesson from building this is practical: memory should carry its assumptions. A record that says “this worked” becomes more useful when the system can also answer “under what conditions, according to which evidence, and do those conditions still hold?”

## An experiment instead of a claim

The System map includes a controlled context experiment. It copies the current
factual snapshot into a disposable FalkorDB graph and removes historical links.
The current incident, deployment, schema, and fixed policy remain unchanged.

Two measured comparisons make the effect inspectable:

| Decision | Connected history | History links removed |
| --- | --- | --- |
| Restart for a matching known failure | Contradicted | Unknown |
| Rollback for a matching known recovery | Supported | Unknown |

The original graph is preserved; temporary graph cleanup and source digests are
tested. These results show that graph context changes this policy's decisions.
They do not establish model accuracy, production reliability, or superiority to
relational storage. A schema-incompatible rollback remains contradicted after
history is removed, because the present-day incompatibility still exists.

## Evidence and scope

The public repository contains 46 passing tests, five synthetic scenario
workflows, two history ablations, the exact Cypher queries, and reproducible setup.
A GitHub Actions run repeats the tests against actual FalkorDB and builds the
frontend on a fresh Linux runner. Remediation remains a simulator, and the
application has one shared workspace rather than per-user authorization.

The durable five-stage workflow can resume completed phases after interruption
when its factual context is unchanged. It is not a distributed recovery service:
individual model/tool calls inside a phase are not checkpointed. The optional
critic is advisory and cannot grant execution authority.

AI coding and writing assistance were used in developing and documenting this
project. The graph experiments and verification artifacts are measured outputs,
not estimates of a hackathon score.

[Source and setup](https://github.com/gowtham66867/recallops-graphhacks) ·
[Architecture](ARCHITECTURE.md) · [Measured evidence](VERIFICATION.md)

