# Three-minute demo script

Before recording: start the app, select Checkout regression, reset that scenario, confirm FalkorDB is connected. Use a wide browser and hide unrelated windows. If no model key is configured, explicitly call the investigation deterministic; do not imply that an LLM is running.

## 0:00–0:20 — Problem

“Your incident agent can remember yesterday’s fix and still give dangerous advice today. RecallOps remembers both the outcome and the conditions under which it worked.”

Show the synthetic incident: 18.4% checkout errors after deployment.

## 0:20–0:50 — Investigation

Show the graph: current incident, Checkout API, deployment, migration, and historical incidents. Briefly scroll to the investigation log to show real bounded tools. Explain whether the current run is deterministic or live.

## 0:50–1:30 — The decision

Click Restart checkout. “This failed for the same signature in incident 17.” Open its source.

Click Roll back checkout. “This worked in incident 21—but on schema v2. The current system has schema v3.” Open the deployment manifest. “Success is conditional memory, not permanent permission.”

## 1:30–2:10 — Approve and act

Click Review simulated action. Show the flag command, preconditions, and state revision. “The rules validate compatibility, and the model has no execution authority.”

Approve and run. “This is a local simulator. It applies a state transition, observes the new error rate, then stores the outcome and lesson in FalkorDB.” Show recovery to 0.2%.

## 2:10–2:40 — Carry experience forward

Click Fresh session. Show a new session ID and the recalled lesson with its signature, schema, and source.

Click Replay with memory. “This explicitly reintroduces the synthetic fault while preserving experience.” Show the recommendation’s added reference to the prior observed success and open the new observation source.

## 2:40–3:00 — Evidence and limits

“FalkorDB supplies the dependency and history traversals and the persistent outcome memory. Removing it produces a visible failure.”

Show the actual results in evaluation.json or VERIFICATION.md. State that the evaluation is a small synthetic deterministic suite and whether the live model has been tested. End on the incident screen.

Recording and publication remain outstanding deliverables; this file is a script, not a recorded video.
