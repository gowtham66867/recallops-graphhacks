# Deployment

The deployable unit is the Python API with the compiled frontend, plus FalkorDB
with an append-only log on a persistent Docker volume. Use a persistent Linux
host with Docker Compose. A standalone stateless Cloud Run service cannot retain
the graph; it requires a separate persistent FalkorDB instance.

Build and start on the host:

```sh
docker compose -f compose.yaml -f compose.deploy.yaml up -d --build --wait
curl --fail http://127.0.0.1:8080/api/health
```

The image runs as an unprivileged user with a read-only filesystem. Its build
context allowlist excludes `.env`, logs, local artifacts, and credentials.
The deployment's model key defaults to empty, even when a local `.env` contains
`OPENAI_API_KEY`. For live mode, set `RECALLOPS_OPENAI_API_KEY` on the deployment
host using a rotated key with available credits, then recreate the app container.

The app and database ports bind to host loopback. For private review on a Google
Compute Engine VM, forward the app port from your computer:

```sh
gcloud compute ssh VM_NAME --project=PROJECT_ID --zone=ZONE -- -N -L 8080:127.0.0.1:8080
```

Open `http://127.0.0.1:8080`. For public access, place an HTTPS reverse proxy with
access control in front of the app. The current app is a shared synthetic
workspace without per-user permissions; do not expose a funded model key to
unrestricted callers. No external remediation integrations are present.

Back up the `recallops-graph` volume before replacing the host or deleting volumes.
Do not use `docker compose down --volumes` when retaining investigations.

## Google Cloud deployment (October 18, 2026)

RecallOps uses a dedicated `recallops-demo` VM in `us-central1-a` (`e2-medium`,
30 GB persistent boot disk), isolated `recallops-network`, and reserved address
`34.46.171.202`. The new VM has no Google service account attached,
and project-wide SSH keys are blocked. SSH is restricted to Google's IAP range;
only TCP 80 and 443 are publicly reachable through the cloud firewall.

The public hostname is `34.46.171.202.sslip.io`. This third-party DNS name resolves
to the reserved IP; Caddy manages HTTPS certificates and redirects HTTP to HTTPS.
The proxy requires a shared demo username and bcrypt-protected password on every
application route. The plaintext password is saved only in the ignored local
`artifacts/deployment-access.txt`; the VM receives its bcrypt hash. Shared demo
credentials provide access control, not per-user authorization or tenant isolation.

The remote source upload uses an explicit file list. It excludes the local `.env`,
API keys, SSH credentials, documents, logs, tests, and artifacts. The Mac's Docker
registry certificate issue is worked around by building on the VM without changing
TLS verification settings. The cloud deployment defaults to deterministic mode.
A previous live-model request returned HTTP 429 `credit_balance_exhausted`.

Connect for maintenance:

```sh
gcloud compute ssh recallops-demo --project=YOUR_PROJECT_ID --zone=us-central1-a --tunnel-through-iap
cd /opt/recallops
sudo docker compose -f compose.yaml -f compose.deploy.yaml -f compose.https.yaml ps
sudo docker compose -f compose.yaml -f compose.deploy.yaml -f compose.https.yaml logs --tail=100
```

Cloud resources incur ongoing charges for the VM, persistent disk, and reserved IP.
Stop the VM when the demo is not needed (the disk and reserved IP still incur
charges):

```sh
gcloud compute instances stop recallops-demo --project=YOUR_PROJECT_ID --zone=us-central1-a
```

The graph resides in a Docker named volume on the boot disk. It survives container
recreation and VM restarts; it is not replicated or automatically backed up. The
boot disk is configured to be deleted with the VM, so back up the graph before
VM deletion. Caddy certificate data also persists in named volumes.

Local verification command after deployment:

```sh
.venv/bin/python -m scripts.smoke_deployment artifacts/deployment-access.txt
```

This checks HTTPS trust, anonymous access rejection, the frontend and five
scenarios, verified investigation, approval enforcement, execution, idempotence,
and lesson retrieval in a fresh session. It modifies only the synthetic
`rollback-valid` scenario. Deployment smoke results are written to the ignored
`artifacts/deployment-smoke.json`.

## Observed validation

The Linux VM image build succeeded. FalkorDB and the app reported healthy, and
Caddy served a trusted HTTPS certificate. The external smoke test passed all five
scenarios, blocked anonymous API requests with HTTP 401, rejected execution before
approval with HTTP 409, completed an approved rollback, returned the same result
on repeat execution, and retrieved one recorded lesson in a new session. The
synthetic error rate recovered to 0.2%. Live model availability was false. The
local full application suite also passed: 46 tests.
