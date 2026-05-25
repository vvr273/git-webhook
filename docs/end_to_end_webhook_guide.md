# End-to-End GitHub Webhook Guide

## Purpose

This document explains the complete GitHub webhook POC from scratch.

It includes:
- local project setup
- Python setup
- Git and GitHub setup
- ngrok setup
- GitHub webhook configuration
- commands to run the service
- commands to collect and save logs
- commands to run the HTML dashboard
- what GitHub event is expected for each GitHub action
- what has been completed already in this POC

This is the single reference document for running and demonstrating the project.

## What This Project Does

This project is a FastAPI service that receives GitHub webhooks and stores normalized metadata for Developer Intelligence analysis.

It does:
- verify GitHub webhook signatures
- normalize supported GitHub events
- store them in SQLite
- expose APIs to inspect events and summary metrics

It does not store:
- code content
- commit diff content
- commit messages
- PR body text
- review body text
- review comment body text

## Current POC Status

The following has already been completed:

- FastAPI webhook service created
- SQLite persistence created
- signature verification implemented
- event normalization implemented
- tests added and passing
- GitHub webhook connected through ngrok
- real `ping` events captured
- real `push` events captured
- JSON reports generated
- local HTML dashboard created

Important note:
- some PR-related events were missed earlier because the ngrok tunnel could not forward requests while the app was unavailable
- the system works, but the app and ngrok must both stay active while GitHub actions are happening

## Project Location

Project root used in this guide:

```text
/home/think41/vishnu/roi/git-webhook
```

## Main Files

Core app:
- [app/main.py](/home/think41/vishnu/roi/git-webhook/app/main.py)
- [app/security.py](/home/think41/vishnu/roi/git-webhook/app/security.py)
- [app/normalizers.py](/home/think41/vishnu/roi/git-webhook/app/normalizers.py)
- [app/models.py](/home/think41/vishnu/roi/git-webhook/app/models.py)
- [app/database.py](/home/think41/vishnu/roi/git-webhook/app/database.py)

Docs and guides:
- [README.md](/home/think41/vishnu/roi/git-webhook/README.md)
- [docs/clear_instructions.md](/home/think41/vishnu/roi/git-webhook/docs/clear_instructions.md)
- [docs/github-webhook-poc-runbook.md](/home/think41/vishnu/roi/git-webhook/docs/github-webhook-poc-runbook.md)
- [docs/end_to_end_webhook_guide.md](/home/think41/vishnu/roi/git-webhook/docs/end_to_end_webhook_guide.md)

Reports and dashboard:
- [reports/events.json](/home/think41/vishnu/roi/git-webhook/reports/events.json)
- [reports/summary.json](/home/think41/vishnu/roi/git-webhook/reports/summary.json)
- [reports/dashboard.html](/home/think41/vishnu/roi/git-webhook/reports/dashboard.html)

Database:
- [github_webhooks.db](/home/think41/vishnu/roi/git-webhook/github_webhooks.db)

## Step 1: Clone or Open the Repository

If cloning fresh:

```bash
git clone https://github.com/vvr273/git-webhook.git
cd git-webhook
```

If already present locally:

```bash
cd /home/think41/vishnu/roi/git-webhook
```

## Step 2: Python Setup

Check Python:

```bash
python3 --version
```

Recommended:
- Python 3.11+

If needed on Ubuntu or Debian:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Create virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
. .venv/bin/activate
```

Install dependencies:

```bash
pip install -e ".[dev]"
```

## Step 3: Environment Configuration

Create `.env`:

```bash
cp .env.example .env
```

Edit `.env` to contain:

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
- the GitHub webhook secret must exactly match `GITHUB_WEBHOOK_SECRET`

## Step 4: Git Setup on Local Machine

Check Git:

```bash
git --version
```

If needed:

```bash
sudo apt update
sudo apt install git
```

Check Git identity:

```bash
git config --global user.name
git config --global user.email
```

Set identity if missing:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## Step 5: GitHub Repository

Repository used in this POC:

```text
https://github.com/vvr273/git-webhook
```

If you need to connect this local folder to GitHub:

```bash
git remote -v
```

If no remote exists:

```bash
git remote add origin https://github.com/vvr273/git-webhook.git
```

## Step 6: Run the FastAPI Service

From the repo root:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Leave this terminal running.

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Step 7: ngrok Setup

Check if ngrok exists:

```bash
ngrok version
```

If not installed:

```bash
sudo snap install ngrok
```

Create or sign in to ngrok account:

```text
https://dashboard.ngrok.com/
```

Get authtoken:

```text
https://dashboard.ngrok.com/get-started/your-authtoken
```

Add token once:

```bash
ngrok config add-authtoken YOUR_REAL_NGROK_TOKEN
```

Run ngrok:

```bash
ngrok http 8000
```

Leave this terminal running.

Expected output contains something like:

```text
Forwarding  https://example.ngrok-free.app -> http://localhost:8000
```

The GitHub webhook endpoint becomes:

```text
https://example.ngrok-free.app/webhooks/github
```

Important:
- if ngrok restarts and gives a new URL, update the GitHub webhook URL too

## Step 8: GitHub Webhook Configuration

Open:

```text
https://github.com/vvr273/git-webhook
```

Then:

1. Go to `Settings`
2. Go to `Webhooks`
3. Click `Add webhook`

Use:

Payload URL:

```text
https://YOUR-NGROK-URL/webhooks/github
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
- choose `Let me select individual events`
- select:
  - `Pushes`
  - `Pull requests`
  - `Pull request reviews`
  - `Pull request review comments`
  - `Workflow runs`
  - `Deployments`
  - `Deployment statuses`

Keep `Active` checked and save.

Expected immediate result:
- GitHub sends a `ping` event

## Step 9: Commands to Inspect Live Data

Show all stored events:

```bash
curl -s http://127.0.0.1:8000/events | python3 -m json.tool
```

Show summary:

```bash
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool
```

Show health:

```bash
curl http://127.0.0.1:8000/health
```

## Step 10: Commands to Save Logs

Create reports folder:

```bash
mkdir -p reports
```

Save events:

```bash
curl -s http://127.0.0.1:8000/events | python3 -m json.tool > reports/events.json
```

Save summary:

```bash
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool > reports/summary.json
```

Save both:

```bash
mkdir -p reports
curl -s http://127.0.0.1:8000/events | python3 -m json.tool > reports/events.json
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool > reports/summary.json
```

## Step 11: Commands to Access SQLite Data Directly

Open database:

```bash
sqlite3 github_webhooks.db
```

Inside SQLite:

```sql
.tables
.schema github_events
SELECT id, delivery_id, event_type, action, repository_full_name, actor_login, occurred_at, received_at
FROM github_events
ORDER BY id DESC;
```

Exit:

```sql
.quit
```

## Step 12: Run the HTML Dashboard

The dashboard reads:
- `reports/events.json`
- `reports/summary.json`

So refresh those first:

```bash
mkdir -p reports
curl -s http://127.0.0.1:8000/events | python3 -m json.tool > reports/events.json
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool > reports/summary.json
```

Start a simple static server from the repo root:

```bash
cd /home/think41/vishnu/roi/git-webhook
python3 -m http.server 8080
```

Open in browser:

```text
http://127.0.0.1:8080/reports/dashboard.html
```

## Step 13: Full Run Flow

Recommended terminal flow:

Terminal 1: webhook app

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2: ngrok

```bash
ngrok http 8000
```

Terminal 3: inspection and saving

```bash
curl http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/events | python3 -m json.tool
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool
mkdir -p reports
curl -s http://127.0.0.1:8000/events | python3 -m json.tool > reports/events.json
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool > reports/summary.json
```

Optional Terminal 4: dashboard

```bash
cd /home/think41/vishnu/roi/git-webhook
python3 -m http.server 8080
```

## Step 14: GitHub Action to Webhook Response Mapping

This section gives the expected GitHub webhook response for each action.

### 1. Add webhook in GitHub

Action:
- create webhook in repository settings

Expected event:
- `ping`

Meaning:
- webhook connection test from GitHub

### 2. Create a branch locally only

Action:
- create branch on local machine

Expected event:
- none

Why:
- local git actions alone do not trigger GitHub webhooks

### 3. Commit locally only

Action:
- commit changes locally

Expected event:
- none

Why:
- commit is not visible to GitHub until pushed

### 4. Push a new branch to GitHub

Action:
- `git push origin <branch>`

Expected event:
- `push`

Important metadata:
- branch
- commit_count
- distinct_commit_count
- head_commit_id
- pusher_name
- pusher_email
- commit_authors

### 5. Push new commit to an existing branch

Action:
- commit and push again

Expected event:
- `push`

### 6. Open a pull request

Action:
- raise PR in GitHub

Expected event:
- `pull_request`

Expected action:
- `opened`

Important metadata:
- `pr_number`
- `pr_id`
- `pr_state`
- `pr_author`
- `base_branch`
- `head_branch`
- `requested_reviewers_count`

### 7. Update a pull request with new commits

Action:
- push more commits to the PR branch

Expected events:
- `push`
- `pull_request`

Expected PR action:
- usually `synchronize`

### 8. Submit a PR review

Action:
- approve, comment, or request changes in review

Expected event:
- `pull_request_review`

Important metadata:
- `review_id`
- `review_state`
- `submitted_at`
- `reviewer_login`

### 9. Add inline PR review comment

Action:
- add inline comment on PR file changes

Expected event:
- `pull_request_review_comment`

Important metadata:
- `comment_id`
- `commenter_login`
- `path_hash`
- `path_extension`

### 10. Merge the PR

Action:
- merge PR in GitHub

Expected event:
- `pull_request`

Expected action:
- `closed`

Important clarification:
- GitHub uses `closed` for both merge and close-without-merge
- you must check `metadata.merged`

Interpretation:
- `action = closed` and `metadata.merged = true` means merged
- `action = closed` and `metadata.merged = false` means closed without merge

### 11. Close PR without merge

Action:
- close PR manually without merging

Expected event:
- `pull_request`

Expected action:
- `closed`

Interpretation:
- `metadata.merged = false`

### 12. GitHub Actions workflow runs

Action:
- workflow starts or completes

Expected event:
- `workflow_run`

Important metadata:
- `workflow_id`
- `workflow_name`
- `run_id`
- `run_number`
- `status`
- `conclusion`
- `run_started_at`
- `duration_seconds`

### 13. Deployment event

Action:
- deployment created

Expected event:
- `deployment`

### 14. Deployment status update

Action:
- deployment status updated

Expected event:
- `deployment_status`

## Step 15: What Response Shape to Expect in Stored Data

All stored events follow a common internal structure:

```json
{
  "id": "<github delivery id>",
  "source": "github",
  "event_type": "<event name>",
  "action": "<payload action if present>",
  "repository": {},
  "actor": {},
  "occurred_at": "<UTC ISO timestamp>",
  "metadata": {}
}
```

## Step 16: Example End-to-End Demo Scenario

Recommended demo:

1. Start FastAPI app
2. Start ngrok
3. Confirm `/health`
4. Confirm GitHub webhook points to current ngrok URL
5. Push a new branch
6. Open PR
7. Review PR
8. Add inline comment
9. Merge PR
10. Save `events.json`
11. Save `summary.json`
12. Open dashboard

This gives the clearest stakeholder demo.

## Step 17: Common Problems

### Problem: `curl: (7) Failed to connect to 127.0.0.1 port 8000`

Cause:
- app not running

Fix:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Problem: GitHub webhook returns `401`

Cause:
- secret mismatch

Fix:
- check `.env`
- check GitHub webhook secret
- they must match exactly
- restart `uvicorn` after `.env` change

### Problem: GitHub webhook returns ngrok error

Cause:
- app not reachable through ngrok

Example:
- `ERR_NGROK_3200`

Fix:
- restart app
- restart ngrok
- verify current ngrok URL
- update GitHub webhook URL if ngrok URL changed
- redeliver missed GitHub events if needed

### Problem: PR events missing from logs

Cause:
- app or ngrok was down during PR activity

Fix:
- redeliver missing events from GitHub webhook Recent Deliveries
- or perform a fresh PR cycle while everything is running

## Step 18: What Has Been Proven in This POC

This POC proves:
- GitHub webhook ingestion works
- signature verification works
- metadata-only storage works
- SQLite storage works
- events can be queried through API
- event summaries can be generated
- saved reports can be rendered in a dashboard

## Step 19: Quick Command Summary

Run app:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run ngrok:

```bash
ngrok http 8000
```

Check health:

```bash
curl http://127.0.0.1:8000/health
```

Show events:

```bash
curl -s http://127.0.0.1:8000/events | python3 -m json.tool
```

Show summary:

```bash
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool
```

Save reports:

```bash
mkdir -p reports
curl -s http://127.0.0.1:8000/events | python3 -m json.tool > reports/events.json
curl -s http://127.0.0.1:8000/metrics/summary | python3 -m json.tool > reports/summary.json
```

Run dashboard:

```bash
cd /home/think41/vishnu/roi/git-webhook
python3 -m http.server 8080
```

Open dashboard:

```text
http://127.0.0.1:8080/reports/dashboard.html
```
