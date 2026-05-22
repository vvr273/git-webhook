# GitHub Webhook Testing Service for Developer Intelligence POC

## Slide 1: Objective

Build a small production-style service that:
- receives GitHub webhooks
- verifies authenticity with HMAC SHA-256
- normalizes metadata only
- stores events for later developer-behavior analysis
- avoids storing code, diffs, PR bodies, and comment text

## Slide 2: Why This POC

We want to validate that GitHub activity alone can support signals like:
- commit throughput
- PR lifecycle behavior
- review participation
- workflow execution patterns
- human vs bot activity
- deployment activity

Without reading source code content.

## Slide 3: What Was Built

FastAPI service with:
- `POST /webhooks/github`
- `GET /health`
- `GET /events`
- `GET /events/{delivery_id}`
- `GET /metrics/summary`

Core modules:
- `app/main.py`
- `app/security.py`
- `app/normalizers.py`
- `app/models.py`
- `app/database.py`
- `app/bot_detection.py`

## Slide 4: Security and Privacy

Security:
- verifies `X-Hub-Signature-256`
- uses shared secret from `GITHUB_WEBHOOK_SECRET`
- verifies raw request body before JSON parsing

Privacy:
- no code content stored
- no commit messages stored
- no PR body stored
- no review body stored
- no review comment body stored
- raw payload disabled by default

## Slide 5: Supported GitHub Events

Currently supported:
- `ping`
- `push`
- `pull_request`
- `pull_request_review`
- `pull_request_review_comment`
- `workflow_run`
- `deployment`
- `deployment_status`

## Slide 6: Normalized Internal Event Model

Each event becomes:

```json
{
  "id": "<delivery id>",
  "source": "github",
  "event_type": "<event>",
  "action": "<action>",
  "repository": {},
  "actor": {},
  "occurred_at": "<UTC timestamp>",
  "metadata": {}
}
```

This gives one consistent structure for downstream analytics.

## Slide 7: Storage Design

Persistence:
- SQLite for local testing
- database file: `github_webhooks.db`

Table:
- `github_events`

Saved fields:
- delivery id
- event type
- action
- repository name
- actor login and type
- bot flag
- occurred_at
- received_at
- normalized payload

## Slide 8: What We Have Proven So Far

Completed:
- service built from scratch
- tests added and passing
- local app running
- ngrok tunnel configured
- GitHub webhook configured
- `ping` event successfully received
- `push` event successfully received
- events stored locally and queryable

Observed on `vvr273/git-webhook`:
- `ping`
- `push`

## Slide 9: Example Captured Push Metadata

Stored metadata for the latest push includes:
- branch: `master`
- commit_count: `1`
- distinct_commit_count: `1`
- head_commit_id
- pusher name and email
- commit authors

Explicitly excluded:
- commit message
- diff content
- file content

## Slide 10: Demo Architecture

Flow:
1. GitHub repo action happens
2. GitHub sends webhook
3. ngrok forwards to local FastAPI
4. FastAPI verifies signature
5. event is normalized
6. event is stored in SQLite
7. events are visible via `/events` and `/metrics/summary`

## Slide 11: Reproduce From Scratch

Commands:

```bash
git clone https://github.com/vvr273/git-webhook.git
cd git-webhook
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Set:

```env
GITHUB_WEBHOOK_SECRET=<shared-secret>
```

Run app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tunnel:

```bash
ngrok http 8000
```

## Slide 12: GitHub Webhook Setup

In repo settings:
- Payload URL: `https://<ngrok-url>/webhooks/github`
- Content type: `application/json`
- Secret: same as `GITHUB_WEBHOOK_SECRET`

Select events:
- Pushes
- Pull requests
- Pull request reviews
- Pull request review comments
- Workflow runs
- Deployments
- Deployment statuses

## Slide 13: How To Run the Demo Live

Start service:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

Show saved events:

```bash
curl http://127.0.0.1:8000/events
```

Show summary:

```bash
curl http://127.0.0.1:8000/metrics/summary
```

Then perform one or more actions in GitHub:
- push a commit
- open PR
- submit PR review
- comment on PR review
- run GitHub Actions workflow

Refresh `/events` and `/metrics/summary`.

## Slide 14: Current Demo Evidence

Current system has already captured:
- `ping` for `vvr273/git-webhook`
- `push` for `vvr273/git-webhook`

This proves:
- GitHub connectivity works
- signature verification works
- ingestion works
- normalization works
- persistence works

## Slide 15: Value for Developer Intelligence

This metadata is enough for future metrics like:
- commits per developer
- PR creation and merge patterns
- review participation rate
- CI completion and friction patterns
- deployment timing
- automation ratio
- human vs bot split
- possible AI-assist proxies based on workflow changes

## Slide 16: Next Steps

Next:
- add repository filters in the API
- add pagination and date filters
- add Postgres for shared environments
- add dashboard views
- trigger PR and workflow events for a richer demo dataset
- add retention and export options
