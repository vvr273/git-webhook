# Project Context

## Purpose

This file is the quick context handoff for future chats.

It summarizes:
- what this project is
- what has been built so far
- where the important files are
- how the system is run
- what documentation exists
- what is still important to remember

## Project Summary

This repository contains a GitHub webhook testing and logging service built with FastAPI for a Developer Intelligence Platform POC.

The system:
- receives GitHub webhooks
- verifies `X-Hub-Signature-256`
- normalizes supported GitHub events into metadata-only records
- stores them locally in SQLite for the POC
- exposes APIs for event inspection and summary metrics
- supports saved reports and a local HTML dashboard
- has now been refactored into cleaner layers so GitHub stays isolated and Jira can be added in the same project structure

The design intentionally avoids storing:
- code content
- commit diff content
- commit messages
- PR body text
- review body text
- review comment body text

## What Has Been Built

### Backend service

Implemented:
- `POST /webhooks/github`
- `GET /health`
- `GET /events`
- `GET /events/{delivery_id}`
- `GET /metrics/summary`

Supported webhook event types:
- `ping`
- `push`
- `pull_request`
- `pull_request_review`
- `pull_request_review_comment`
- `workflow_run`
- `deployment`
- `deployment_status`

Current backend package layout:
- `app/api/`
- `app/core/`
- `app/db/`
- `app/integrations/github/`
- `app/integrations/jira/`

Important backend files:
- [app/main.py](/home/think41/vishnu/roi/git-webhook/app/main.py)
- [app/api/routes/github_webhooks.py](/home/think41/vishnu/roi/git-webhook/app/api/routes/github_webhooks.py)
- [app/api/routes/events.py](/home/think41/vishnu/roi/git-webhook/app/api/routes/events.py)
- [app/api/routes/metrics.py](/home/think41/vishnu/roi/git-webhook/app/api/routes/metrics.py)
- [app/api/routes/health.py](/home/think41/vishnu/roi/git-webhook/app/api/routes/health.py)
- [app/core/config.py](/home/think41/vishnu/roi/git-webhook/app/core/config.py)
- [app/core/security.py](/home/think41/vishnu/roi/git-webhook/app/core/security.py)
- [app/db/database.py](/home/think41/vishnu/roi/git-webhook/app/db/database.py)
- [app/db/models.py](/home/think41/vishnu/roi/git-webhook/app/db/models.py)
- [app/integrations/github/normalizers.py](/home/think41/vishnu/roi/git-webhook/app/integrations/github/normalizers.py)
- [app/integrations/github/service.py](/home/think41/vishnu/roi/git-webhook/app/integrations/github/service.py)
- [app/integrations/github/bot_detection.py](/home/think41/vishnu/roi/git-webhook/app/integrations/github/bot_detection.py)
- [app/integrations/jira/README.md](/home/think41/vishnu/roi/git-webhook/app/integrations/jira/README.md)

Compatibility wrappers still exist at the top level:
- [app/config.py](/home/think41/vishnu/roi/git-webhook/app/config.py)
- [app/security.py](/home/think41/vishnu/roi/git-webhook/app/security.py)
- [app/database.py](/home/think41/vishnu/roi/git-webhook/app/database.py)
- [app/models.py](/home/think41/vishnu/roi/git-webhook/app/models.py)
- [app/normalizers.py](/home/think41/vishnu/roi/git-webhook/app/normalizers.py)
- [app/bot_detection.py](/home/think41/vishnu/roi/git-webhook/app/bot_detection.py)

These wrappers forward to the new package structure so older imports do not break immediately.

### Persistence

Current POC storage:
- SQLite database file: [github_webhooks.db](/home/think41/vishnu/roi/git-webhook/github_webhooks.db)

Table:
- `github_events`

Stored fields include:
- delivery id
- event type
- action
- repository
- actor
- bot flag
- occurred_at
- received_at
- normalized payload

### Tests

Pytest coverage exists for:
- valid signature accepted
- invalid signature rejected
- ping event handling
- push normalization without commit messages
- PR normalization without PR body
- bot detection
- duplicate delivery id behavior

Test file:
- [tests/test_webhooks.py](/home/think41/vishnu/roi/git-webhook/tests/test_webhooks.py)

### Reports and dashboard

Saved reports:
- [reports/events.json](/home/think41/vishnu/roi/git-webhook/reports/events.json)
- [reports/summary.json](/home/think41/vishnu/roi/git-webhook/reports/summary.json)

Dashboard:
- [reports/dashboard.html](/home/think41/vishnu/roi/git-webhook/reports/dashboard.html)

Dashboard capabilities currently include:
- total event cards
- push / PR / workflow summary cards
- repository coverage view
- event type mix view
- recent activity list
- event interpretation improvements for PR merge vs closed-without-merge
- filters for:
  - repository name
  - single user id / login
  - group of users via comma-separated input

### Extensibility direction

The project is now structurally ready for the next platform integration.

Current intent:
- GitHub remains under `app/integrations/github/`
- Jira should be implemented under `app/integrations/jira/`
- future identity mapping can be added without mixing provider logic into core route code

## What Has Been Proven

The POC has already demonstrated:
- live GitHub webhook receipt
- valid `ping` event storage
- valid `push` event storage
- multiple repositories can point to one backend
- event data can be queried from API
- event data can be saved as JSON reports
- saved reports can be visualized in a local dashboard
- the backend can be refactored into cleaner layers without breaking behavior

Important earlier issue:
- some PR-related deliveries were missed when ngrok or the local app was unavailable
- the implementation itself worked, but local uptime/tunnel continuity mattered

## Current Operating Model

### Local / POC mode

Flow:

```text
GitHub -> ngrok public URL -> local FastAPI app -> SQLite
```

Use this when:
- testing locally
- validating webhooks quickly
- demoing the POC

### Scaled / org-wide direction

Recommended future flow:

```text
GitHub App or many repo webhooks -> deployed public backend -> PostgreSQL
```

Use this when:
- many repos must be tracked
- many users must be observed within tracked repos
- the service must be always on
- ngrok should be removed from the architecture
- Jira or other provider integrations must live beside GitHub cleanly

## Important Scope Clarifications

The current webhook model can capture:
- GitHub-visible repository activity
- activity from all users acting in tracked repositories
- activity from branches that generate supported webhook events

The current model cannot capture:
- local commits that were never pushed
- local branch creation that never reached GitHub
- local terminal git commands
- universal user activity outside integrated repositories

## Main Documentation Available

Primary documents:
- [docs/imp_docs/github-webhook.md](/home/think41/vishnu/roi/git-webhook/docs/imp_docs/github-webhook.md)
- [docs/end_to_end_webhook_guide.md](/home/think41/vishnu/roi/git-webhook/docs/end_to_end_webhook_guide.md)
- [docs/response_interpretation_guide.md](/home/think41/vishnu/roi/git-webhook/docs/response_interpretation_guide.md)
- [docs/github_webhook_possibilities.md](/home/think41/vishnu/roi/git-webhook/docs/github_webhook_possibilities.md)
- [docs/org_wide_github_setup.md](/home/think41/vishnu/roi/git-webhook/docs/org_wide_github_setup.md)
- [docs/clear_instructions.md](/home/think41/vishnu/roi/git-webhook/docs/clear_instructions.md)
- [docs/github-webhook-poc-runbook.md](/home/think41/vishnu/roi/git-webhook/docs/github-webhook-poc-runbook.md)
- [commands.txt](/home/think41/vishnu/roi/git-webhook/commands.txt)

This file:
- [docs/context/project_context.md](/home/think41/vishnu/roi/git-webhook/docs/context/project_context.md)

## Commands Commonly Used

Run the app:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run ngrok:

```bash
ngrok http 8000
```

Health:

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

## Expected Future Work

Likely next improvements:
- backend filters for repo / user / group / branch / date range
- better PR-specific reporting
- PostgreSQL migration for shared deployment
- deployed public webhook receiver
- GitHub App based org-wide ingestion
- real Jira integration under `app/integrations/jira/`
- identity mapping for SSO + GitHub + Jira style cross-tool linking

## Update Rule

Whenever a feature is added, changed, or materially clarified:
- update this file
- add the feature under the appropriate section
- record any new important files
- record any new commands if usage changed
- record any new scope clarification if the product meaning changed
