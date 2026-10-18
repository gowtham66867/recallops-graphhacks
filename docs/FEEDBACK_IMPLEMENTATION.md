# RecallOps adaptation of the 35-item feedback register

The feedback supplied by the user concerned MerchantLens. It is adapted here to
incident response. No statement is attributed to a Paytm leader in RecallOps,
and no Paytm integration, payment verification, financial ROI, or production
certification is claimed.

Open [Responder context](https://34.46.171.202.sslip.io/?view=handoff).

| Item | RecallOps response | Status / limit |
| --- | --- | --- |
| F01 Adaptive investigation | Existing six evidence tools, specialists, current preconditions | Implemented; deterministic hosted mode |
| F02 Verifiability | Exact source text and IDs in reviewed internal handoff | Implemented; existence and linkage are not semantic truth |
| F03 Separate signals | Operator reports, synthetic telemetry, forecasts, and recorded simulator outcomes remain distinct | Implemented; no financial-loss inference |
| F04 Claims and gaps | Reports stay unverified; explicit unknowns travel in the handoff | Implemented |
| F05 Model context | Graph conditions, histories, lessons, and latest 12 active operator reports | Implemented; omitted active count exposed; full timeline retained for review |
| F06 Corrections and approval | New correction source supersedes an earlier report; context digest invalidates reviews | Implemented; no cryptographic human signature |
| F07 Communication | Typed assessment, critic verdict, validated specialist envelopes, durable JSON stages | Implemented; same-process orchestration, no A2A protocol |
| F08 Agent concepts | Parallel read-only collection, structured synthesis, critique, conditional handoff | Existing architecture retained |
| F09 Harness | Code owns source admission, call/repair/time budgets and execution authority | Implemented |
| F10 Bounds | At most 8 researcher requests plus 1 critic, 12 researcher tool calls, 1 assessment repair, 120s shared invocation budget | Implemented; per-network-operation timeouts, not a process-kill deadline; resume gets a fresh invocation budget |
| F11 Inspectability | Actual tool trace, model request count, code limits and source fingerprint | Implemented; token counts currently cover researcher only |
| F12 Ablation | Remove historical graph links in a disposable real graph | Existing measured rule experiment; no causal/model-accuracy claim |
| F13 Guardrails | Untrusted reports and record text; models cannot approve/execute | Implemented; reports cannot establish action eligibility |
| F14 Exit / failure | Abstain on unknowns; interrupted stages retained; human review available immediately | Implemented; no background autonomous remediation |
| F15 Reliable dictation | Optional server-side Gemini transcription into an editable draft | Implemented, unconfigured and live-unverified in this project |
| F16 Languages | English/Hindi/Kannada/Hinglish report language and localized procedural prompts | Implemented; operational summaries remain English, real-language quality unmeasured |
| F17 Wispr | External dictation can enter the note field | Compatible; no Wispr API integration |
| F18 Voice provider | Separate Gemini audio configuration; original OpenAI investigator remains optional | Implemented; no GPT Live connection and no cross-project key reuse |
| F19 Pause detection | Optional energy gate with 1.2/2/3.5s pause choices | Implemented; heuristic, not semantic VAD |
| F20 Recording limits | 200ms sustained energy, 10s no-speech discard, 45s/4MiB cap, generation cancellation | Implemented; manual Stop available; noisy-room behavior unmeasured |
| F21 Playback | Device voice, optional Gemini Kore TTS, explicit Read/Stop controls | Implemented; installed voice/provider availability varies |
| F22 Codecs | Preferred WebM/Opus, MP4/Ogg browser fallbacks; validated WAV or PCM wrapped as WAV | Contract tests cover 24kHz mono 16-bit output; actual browser codec varies |
| F23 Refresh reliability | Spoken preference, provider, language and pause setting survive reload | Browser verified; consent intentionally does not persist; click Read after refresh |
| F24 Evaluations | 87 Python tests, 8 frontend tests, five scenario cases and two ablations | Observed checks, not an accuracy benchmark; provider contracts are mocked |
| F25 Deployment | Existing password-protected HTTPS VM/FalkorDB deployment | Shared demo authentication retained |
| F26 Privacy | Common-secret masking, explicit audio consent, audience-specific reviewed exports, report redaction | Incomplete PII detection; provider retention and downloaded copies are outside app deletion |
| F27 Consistency | Mutation leases, source digest, audience approvals; redaction excludes active workflows | Implemented; no tenant authorization or enterprise identity |
| F28 Evidence honesty | Existing captioned core video plus current UI captures and verification records | Core video predates this upgrade; audio provider success not claimed |
| F29 Branding | RecallOps identity and domain remain unchanged | No imported comparison-project branding |
| F30 Prior support layers | Existing five workflow stages plus source-linked operator response history | Generic incident workflow; no claim about Paytm's internal layers |
| F31 Avoid repeated attempts | Prior attempts and their reported outcomes travel into the handoff | Manual reports remain unverified; they do not replace native outcome evidence |
| F32 Human access | Request review with zero completed investigations or reports | Local packet/flag only; no human connected or external ticket sent |
| F33 ROI | Proposed reviewer-led incident pilot below | Savings and business impact not measured |
| F34 Integrations | Read-only telemetry/history and reviewed idempotent ticket adapters documented as next step | Requires authorized APIs and identities; not connected |
| F35 Existing practices | Distinguish prototype memory and handoff value from existing incident tooling | No claim that graphs or staged support are unique |

## Test the implemented flow

1. Save a prior attempt in Responder context. It is labeled an unverified report
   and receives a source ID; telemetry and action eligibility do not change.
2. Correct it using a new source. The earlier account remains visible.
3. Request a handoff, inspect the entire internal or anonymized payload, explicitly
   approve that audience, then download. A different audience needs its own approval.
4. Add context or change incident state. The server rejects exports of the old
   packet until a new packet is reviewed and approved.
5. Redact a report after reviewing the confirmation. Its source text and retained
   run/review copies are removed. Downloaded/provider-side copies cannot be recalled.
6. Enable spoken prompts, refresh, and verify the preference remains enabled.
   Read requires a click. Gemini recording/playback require a configured key and
   per-tab consent; device playback requires an installed matching voice.

## Production acceptance work

Agree authorized telemetry/history/ticket APIs, identity, tenant boundaries,
retention/deletion, backup recovery, distributed request and spend controls,
and monitoring before using real incidents. Evaluate a reviewer-labeled pilot
with at least 10 representative incidents, including unknowns and corrections.
Measure time to an accepted handoff, repeated questions and attempted fixes,
reviewer corrections, confirmed recovery/recontacts, language/audio failures,
latency, and cost. Set thresholds and a baseline before the pilot. No pilot has
been run and no ROI or model-accuracy result is inferred from synthetic tests.

Audio implementation follows [Google audio understanding](https://ai.google.dev/gemini-api/docs/audio)
and [speech generation](https://ai.google.dev/gemini-api/docs/generate-content/speech-generation).
SDK retries remain disabled; see [OpenAI rate limits](https://developers.openai.com/api/docs/guides/rate-limits).
