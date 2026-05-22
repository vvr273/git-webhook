# GitHub Webhook Testing Service POC Runbook

## Purpose

This document is the operator runbook for the GitHub webhook testing service POC.

It covers:
- what has been completed so far
- what is currently working
- prerequisites and environment setup
- GitHub and ngrok setup
- two ways to demonstrate the system
- where event data is stored
- how to inspect the captured data

This is written as an execution guide for a senior reviewer or engineer who wants to reproduce the flow without guessing.

## Current Status

The following work has already been completed in `/home/think41/vishnu/roi/git-webhook`:

- Built a FastAPI webhook ingestion service
- Implemented GitHub webhook signature verification using `X-Hub-Signature-256`
- Implemented normalization for supported GitHub event types
- Added SQLite persistence
- Added idempotency using GitHub delivery id
- Added test coverage with `pytest`
- Connected the service to GitHub using `ngrok`
- Configured a webhook on `vvr273/git-webhook`
- Successfully captured live GitHub events

## Verified Live Results

The service has already received and stored real events.

Confirmed event types so far:
- `ping`
- `push`

Confirmed repository:
- `vvr273/git-webhook`

Current local inspection endpoints:
- `GET /health`
- `GET /events`
- `GET /events/{delivery_id}`
- `GET /metrics/summary`

## What the Service Stores

This service stores normalized metadata only.

Stored examples:
- event type
- action
- repository name
- actor login and actor type
- bot vs human flag
- UTC timestamps
- push metadata such as branch, commit count, distinct commit count, head SHA, pusher identity, commit authors
- PR metadata such as counts and lifecycle timestamps
- workflow run metadata such as status and duration
- deployment metadata

This service does not store:
- code content
- commit diff content
- commit messages
- PR body text
- review body text
- review comment body text

## Where the Data Is Stored

The local persistent store is:
- [github_webhooks.db](/home/think41/vishnu/roi/git-webhook/github_webhooks.db)

Database table:
- `github_events`

This file will continue accumulating webhook event records as long as the app is running and GitHub can reach the webhook URL.

## Project Files

Core project files:
- [pyproject.toml](/home/think41/vishnu/roi/git-webhook/pyproject.toml)
- [README.md](/home/think41/vishnu/roi/git-webhook/README.md)
- [app/main.py](/home/think41/vishnu/roi/git-webhook/app/main.py)
- [app/security.py](/home/think41/vishnu/roi/git-webhook/app/security.py)
- [app/normalizers.py](/home/think41/vishnu/roi/git-webhook/app/normalizers.py)
- [app/database.py](/home/think41/vishnu/roi/git-webhook/app/database.py)
- [app/models.py](/home/think41/vishnu/roi/git-webhook/app/models.py)
- [tests/test_webhooks.py](/home/think41/vishnu/roi/git-webhook/tests/test_webhooks.py)

## Prerequisites

Required locally:
- Python 3.11+
- `git`
- `ngrok`
- GitHub repository admin access for webhook configuration

Optional but recommended:
- GitHub account authenticated locally for pushing changes
- `openssl` for generating a webhook secret

## One-Time Environment Setup

Run these commands from the repo root:

```bash
cd /home/think41/vishnu/roi/git-webhook
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Set a webhook secret in `.env`:

```env
GITHUB_WEBHOOK_SECRET=<your-shared-secret>
DATABASE_URL=sqlite:///./github_webhooks.db
STORE_RAW_PAYLOAD=false
LOG_LEVEL=INFO
```

Generate a strong secret if needed:

```bash
openssl rand -hex 32
```

Important:
- the GitHub webhook secret and `GITHUB_WEBHOOK_SECRET` must match exactly
- if `.env` changes, restart the FastAPI app

## Start the Service

From the repo root:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## ngrok Setup

If `ngrok` is not installed:

```bash
sudo snap install ngrok
```

Get your ngrok authtoken from:
- `https://dashboard.ngrok.com/get-started/your-authtoken`

Configure ngrok once:

```bash
ngrok config add-authtoken <your-ngrok-token>
```

Start the tunnel:

```bash
ngrok http 8000
```

Example output:

```text
Forwarding  https://example-name.ngrok-free.app -> http://localhost:8000
```

Webhook endpoint to use in GitHub:

```text
https://example-name.ngrok-free.app/webhooks/github
```

## GitHub Webhook Setup

Repository used for this POC:
- `https://github.com/vvr273/git-webhook`

In GitHub:

1. Open the repository
2. Go to `Settings -> Webhooks -> Add webhook`
3. Configure the webhook as follows:

Payload URL:
```text
https://<your-ngrok-url>/webhooks/github
```

Content type:
```text
application/json
```

Secret:
```text
same exact value as GITHUB_WEBHOOK_SECRET
```

Event selection:
- Choose `Let me select individual events`
- Select:
  - `Pushes`
  - `Pull requests`
  - `Pull request reviews`
  - `Pull request review comments`
  - `Workflow runs`
  - `Deployments`
  - `Deployment statuses`

Keep `Active` checked.

Expected behavior after saving:
- GitHub sends a `ping` event immediately
- the service should receive and store it

## Basic Inspection Commands

List all stored events:

```bash
curl http://127.0.0.1:8000/events
```

Get a single event by delivery id:

```bash
curl http://127.0.0.1:8000/events/<delivery_id>
```

Get summary metrics:

```bash
curl http://127.0.0.1:8000/metrics/summary
```

## Demo Path 1: Build and Run From Scratch

Use this flow if the goal is to demonstrate setup and system assembly.

### Step 1: Clone the repository

```bash
git clone https://github.com/vvr273/git-webhook.git
cd git-webhook
```

### Step 2: Create and activate the environment

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

### Step 3: Set the secret

Edit `.env` and set:

```env
GITHUB_WEBHOOK_SECRET=<shared-secret>
```

### Step 4: Start FastAPI

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Start ngrok in a second terminal

```bash
ngrok http 8000
```

### Step 6: Configure the GitHub webhook

Use:
- Payload URL: `https://<ngrok-url>/webhooks/github`
- Content type: `application/json`
- Secret: same as `.env`

### Step 7: Verify the system

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/events
curl http://127.0.0.1:8000/metrics/summary
```

Expected first event:
- `ping`

This path demonstrates that the system can be created, configured, exposed, and validated from zero.

## Demo Path 2: Run, Trigger Events, and Show Stored Data

Use this flow if the goal is to demonstrate operational value and collected event evidence.

### Step 1: Start the service

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 2: Start ngrok

```bash
ngrok http 8000
```

### Step 3: Confirm health

```bash
curl http://127.0.0.1:8000/health
```

### Step 4: Trigger real GitHub actions

Supported actions that will generate stored events:
- push a commit to `vvr273/git-webhook`
- open a pull request
- update a pull request
- merge a pull request
- submit a pull request review
- add an inline review comment
- run a GitHub Actions workflow
- create a deployment or deployment status

### Step 5: Show collected event data

```bash
curl http://127.0.0.1:8000/events
curl http://127.0.0.1:8000/metrics/summary
```

### Step 6: Explain what is being stored

For a `push` event, show that the system stores:
- repository
- actor
- branch
- commit counts
- head commit SHA
- pusher identity
- commit authors
- timestamps

And does not store:
- commit messages
- code diffs
- file contents

This path demonstrates that real GitHub activity is ingested and saved as safe analytics metadata.

## Recommended Demo Narrative for a Senior Audience

Use this sequence:

1. Show the app is running with `/health`
2. Show that the database starts with existing events via `/events`
3. Trigger a real GitHub action such as a push or PR update
4. Refresh `/events`
5. Highlight the new record for `vvr273/git-webhook`
6. Show `/metrics/summary`
7. Explain that the system stores developer workflow metadata, not code content
8. Point to the local database file as the source of persisted evidence

## Current Evidence Available Now

At the time of writing, the local service has already captured live events for:
- `vvr273/git-webhook`

Observed event types so far:
- `ping`
- `push`

You can inspect them immediately with:

```bash
curl http://127.0.0.1:8000/events
```

## Troubleshooting

### `curl: (7) Failed to connect to 127.0.0.1 port 8000`

Cause:
- FastAPI is not running

Fix:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### GitHub webhook returns `401`

Cause:
- webhook secret mismatch

Fix:
- make sure GitHub `Secret` exactly matches `GITHUB_WEBHOOK_SECRET`
- restart the app after changing `.env`

### GitHub webhook does not arrive

Cause:
- ngrok not running
- wrong payload URL
- webhook configured on the wrong repository

Fix:
- confirm `ngrok http 8000` is active
- confirm the GitHub webhook URL points to `/webhooks/github`
- confirm the webhook exists on `vvr273/git-webhook`

### GitHub webhook payload uses form encoding

Cause:
- webhook `Content type` is set incorrectly

Fix:
- change GitHub webhook `Content type` to `application/json`

## What This POC Proves

This POC proves that GitHub webhooks can provide a safe metadata layer for Developer Intelligence use cases.

Specifically, it proves:
- GitHub webhook ingestion is feasible
- signature verification can be enforced
- events can be normalized into one internal model
- useful engineering workflow metadata can be persisted without storing source code content
- the resulting event stream can support future metrics around productivity, automation, review behavior, CI activity, and deployment flow

## Next Logical Extensions

Recommended next steps:
- add API filtering by repository and date
- add pagination for `/events`
- add export support
- add Postgres for multi-user/shared deployment
- add dashboards or notebooks on top of the normalized event data
- generate PR, review, and workflow events on `vvr273/git-webhook` to broaden the live dataset
