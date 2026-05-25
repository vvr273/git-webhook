# Organization-Wide GitHub Activity Logging Setup

## Purpose

This document explains how to expand the current GitHub webhook POC from a single repository setup into an organization-wide GitHub activity logging system.

It is written for teams who want to capture GitHub-visible engineering workflow activity across many repositories, many contributors, and many branches.


This document covers:
- what can and cannot be captured
- the recommended architecture
- how to capture activity across an organization
- how to cover all users acting in organization repositories
- how to cover all branches that generate GitHub activity
- the difference between repository webhooks and GitHub Apps
- setup recommendations for a scalable production model

## Important Clarification

This system captures GitHub-visible activity, not every local git command run on a developer laptop.

That means it can capture:
- pushes to GitHub
- pull request creation and lifecycle
- pull request reviews
- pull request review comments
- workflow runs
- deployments
- deployment status updates

It cannot capture:
- local commits that were never pushed
- local branch creation that was never pushed
- local rebases before push
- local reset/amend operations that never reached GitHub
- terminal-level git commands on user machines

So the correct scope statement is:

- organization-wide GitHub activity logging

not:

- every local git action ever performed on every laptop

## What “All Users” Means

In an organization-wide GitHub integration, “all users” should be interpreted as:

- all GitHub users who perform actions inside the repositories covered by the integration

This includes:
- organization members
- repository collaborators
- external contributors opening PRs
- automation bots such as Dependabot
- `github-actions[bot]`

This does not mean:
- every action that those users perform outside the tracked repositories

## What “All Branches” Means

In this model, “all branches” means:

- all branches that generate GitHub events in the tracked repositories

Examples:
- push to `main`
- push to `develop`
- push to `feature/payment-refactor`
- push to PR source branches
- PR branch updates that trigger `push` or `pull_request` events

Important clarification:

- this is event-driven branch visibility
- this is not automatically a complete branch inventory system

If a branch never generates a webhook event, the system may never see it.

If full branch inventory is required, add scheduled GitHub API sync jobs.

## What the Current POC Is

The current POC is:
- repository-specific
- webhook-based
- suitable for proof of concept and local validation

Current architecture:

```text
GitHub Repository
    -> Repository Webhook
    -> Public URL
    -> FastAPI Receiver
    -> Signature Verification
    -> Event Normalization
    -> SQLite Storage
```

This is enough to prove ingestion works, but it is not the best long-term design for organization-wide coverage.

## Recommended Organization-Wide Architecture

For organization-scale coverage, the recommended architecture is:

```text
GitHub Organization
    -> GitHub App
    -> Webhook Events
    -> Public Backend Endpoint
    -> Signature Verification
    -> Event Normalization
    -> PostgreSQL Storage
    -> APIs / Reports / Dashboards / Analytics
    -> Optional Scheduled Sync Jobs
```

This is the preferred approach because it is more scalable, easier to govern, and better aligned with production rollout.

## Why Use a GitHub App Instead of Manual Repo Webhooks

Repository webhooks are acceptable for a POC, but organization-wide rollout is better with a GitHub App.

Benefits of a GitHub App:
- centralized installation model
- easier rollout across many repositories
- permission control is clearer
- lifecycle management is better
- easier onboarding of new repositories
- more production-ready for org-level telemetry

Manual repository webhooks become difficult to manage when the number of repositories grows.

## Recommended Scope Model

For organization-wide logging, the recommended scope is:

- all repositories in the organization, or
- a selected rollout group first, then all repositories later

The installation can be phased:

### Phase 1
- install on a few pilot repositories
- validate ingestion and storage

### Phase 2
- install on a business unit or engineering group

### Phase 3
- install on all repositories in the organization

## Events to Capture

Recommended webhook events for Developer Intelligence style ingestion:

- `ping`
- `push`
- `pull_request`
- `pull_request_review`
- `pull_request_review_comment`
- `workflow_run`
- `deployment`
- `deployment_status`

These are enough to capture:
- code push activity
- branch activity
- PR lifecycle
- review participation
- CI/CD signals
- deployment signals

## What Repository-Level Coverage Means at Org Scale

If the GitHub App is installed across all repositories in the organization, then the system can capture:

- all supported GitHub events across those repositories
- all contributors acting in those repositories
- all branches that generate supported events

In practical terms:

- pushes in repo A are captured
- PRs in repo B are captured
- workflow runs in repo C are captured
- reviews in repo D are captured

All of these can be stored in one normalized event pipeline, separated by repository metadata.

## Required Backend Changes for Organization-Scale Use

The current local POC should be extended for broader rollout.

## 1. Replace SQLite with PostgreSQL

SQLite is fine for local testing.

For organization-wide ingestion, use:
- PostgreSQL

Why:
- better concurrency
- better durability
- easier operations
- better indexing and filtering
- better support for analytics workloads

## 2. Add Organization-Aware Fields

Recommended additional fields:
- `organization_login`
- `installation_id`
- `repository_id`
- `repository_full_name`
- `default_branch`
- `branch`
- `actor_login`
- `actor_type`
- `is_bot`

These help support organization-wide queries later.

## 3. Keep Idempotency

Keep:
- `delivery_id` unique

This prevents duplicate webhook rows during retries or redeliveries.

## 4. Keep Metadata-Only Privacy Model

Recommended:
- do not store code content
- do not store commit diff content
- do not store PR body text
- do not store review body text
- do not store review comment body text

This helps reduce data sensitivity and is a strong design choice for a Developer Intelligence ingestion layer.

## 5. Add Filtering APIs

For organization-scale usage, the API should eventually support:
- filter by organization
- filter by repository
- filter by branch
- filter by actor
- filter by event type
- filter by date range

## 6. Add Scheduled Sync Jobs

Webhooks are great for near-real-time events.

But org-scale systems benefit from sync jobs too.

Recommended sync jobs:
- repository inventory sync
- branch inventory sync
- organization member mapping
- team-to-repository mapping
- historical backfill if needed

This creates a stronger system than webhooks alone.

## Recommended Deployment Model

Do not use ngrok for an organization-wide production rollout.

Instead, host the webhook receiver at a stable public HTTPS endpoint such as:

```text
https://github-events.yourcompany.com/webhooks/github
```

Possible hosting options:
- AWS
- GCP
- Azure
- Kubernetes
- Render
- Fly.io
- Railway
- internal platform with public ingress

Requirements:
- stable HTTPS URL
- reliable uptime
- secure secret storage
- observability and logs

## GitHub App Setup Instructions

## Step 1: Create a GitHub App

In GitHub:

1. Open Developer Settings
2. Create `New GitHub App`
3. Set:
   - app name
   - homepage URL
   - webhook URL
   - webhook secret

Webhook URL example:

```text
https://github-events.yourcompany.com/webhooks/github
```

## Step 2: Subscribe to Webhook Events

Enable:
- `push`
- `pull_request`
- `pull_request_review`
- `pull_request_review_comment`
- `workflow_run`
- `deployment`
- `deployment_status`

## Step 3: Configure App Permissions

Recommended read-focused permissions:

- Repository metadata: `Read`
- Pull requests: `Read`
- Actions: `Read`
- Deployments: `Read`

Keep permissions as minimal as possible.

## Step 4: Install the App

Install the app on:
- all repositories in the organization, or
- a selected subset for phased rollout

If the goal is broad coverage, install on all repositories that are in scope.

## Step 5: Verify Installation

After installation:
- GitHub should begin sending events from installed repositories
- the backend should verify and store them
- organization and repository identifiers should be visible in stored records

## Practical Coverage Questions

## “Can this capture all users in the organization?”

Yes, if they perform GitHub actions inside repositories where the app is installed.

## “Can this capture all repositories in the organization?”

Yes, if the app is installed on all of them.

## “Can this capture all branches in those repositories?”

Yes, if branch activity produces supported webhook events.

## “Can this capture all local git commands on developer laptops?”

No.

That would require endpoint-level telemetry or developer workstation instrumentation, which is not what GitHub webhooks provide.

## “Can this support cross-repository analytics?”

Yes.

That is one of the main reasons to centralize ingestion across repositories.

## Recommended Rollout Plan

## Stage 1: Pilot

- deploy webhook receiver publicly
- use PostgreSQL
- create GitHub App
- install on 2 to 5 repositories
- validate event ingestion

## Stage 2: Controlled Expansion

- install on a broader repository set
- add dashboards and repository filters
- add sync jobs

## Stage 3: Organization-Wide Rollout

- install on all repositories in scope
- enable structured monitoring
- add retention policies
- support downstream analytics and reporting

## What This Makes Possible

With org-wide GitHub webhook ingestion, you can later support:

- repository activity timelines
- branch activity tracking
- PR lifecycle measurement
- review participation tracking
- workflow success/failure tracking
- deployment activity tracking
- human vs bot activity split
- cross-repository engineering workflow analysis

## What This Still Does Not Mean

Even with org-wide setup, this system still should not be described as:

- full code understanding
- full local git telemetry
- exact developer productivity scoring
- complete explanation of engineering intent

It is best described as:

- organization-wide GitHub activity metadata ingestion

That is both accurate and defensible.

## Recommended Summary Statement

Use this wording when explaining the setup:

“By installing a GitHub App across the organization’s repositories, we can capture GitHub-visible engineering workflow activity across all installed repositories, all contributors acting in those repositories, and all branches that generate supported webhook events. This includes pushes, pull requests, reviews, workflow runs, and deployments, while intentionally avoiding storage of code content and diff content.”
