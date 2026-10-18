# Yesterday’s successful fix can be today’s wrong answer

An incident agent remembers that a rollback worked. Then a schema migration lands. The next outage looks familiar, so the agent recommends the same rollback. The memory is accurate; the advice is outdated.

That is the problem behind RecallOps. I wanted an incident assistant to preserve the conditions behind an outcome, not just a sentence saying “rollback fixed checkout.”

The prototype uses a fictional commerce system. FalkorDB connects current incidents to services, deployments, migrations, historical attempts, observed outcomes, and original source records. The investigation can follow the path from today’s checkout incident through the service to an earlier attempt and its result. A separate deployment-to-migration path describes the system as it is now.

The useful comparison happens where those paths meet. Did the historical action assume schema v2? Is the current schema v3? A deterministic compatibility check can reject that action even when a retrieved postmortem sounds persuasive. Missing telemetry remains unknown rather than becoming permission.

The demonstration also records a failed restart. Remembering failure is useful because an agent can otherwise repeat an attractive but ineffective action. RecallOps ties that failure to its observed signature; it does not ban every future restart because one once failed.

A user reviews the supported action before execution. Everything runs in a clearly labeled local simulator. The simulator applies explicit transition rules and generates observations. An endpoint returning successfully is not the recovery criterion: the observed error rate must fall below the configured threshold.

The resulting attempt, outcome, source, and conditional lesson are committed together in one FalkorDB query. A new application session reads that durable graph. A replay control explicitly reintroduces the fictional fault while retaining experience, making it possible to inspect how the newly recorded outcome supplements the next recommendation.

The model’s role is deliberately bounded. An optional Responses API agent can investigate through read-only tools and explain the evidence. Deterministic checks govern action applicability, and the model cannot approve execution. Without a configured API key, the application labels its investigation as deterministic. The live provider path remains unverified until it is exercised with a configured account.

The evaluation is intentionally modest: predefined synthetic scenarios, real FalkorDB integration tests, and measured results kept in the repository. It establishes specific implementation behaviors, not production incident accuracy or superiority to every other database architecture.

The lesson from building this is practical: memory should carry its assumptions. A record that says “this worked” becomes more useful when the system can also answer “under what conditions, according to which evidence, and do those conditions still hold?”

Draft for human review. Update the narrative to reflect the submitter’s actual experience before publication.
