# GitHub Webhook Logging and Ingestion Guide



---

## 1. Purpose

This document explains how to bring GitHub activity data into our system using GitHub Webhooks.

The goal is to define:

- What GitHub events can be logged
- What information should be extracted from each event
- How to configure GitHub Webhooks
- How to expose a local service using ngrok for development/testing
- How the backend should receive, verify, normalize, and store webhook logs
- How to interpret the raw logs safely
- What data is available for downstream derivations

This document focuses only on the logging and ingestion layer.

Once the data is collected, other teams or later stages can build analytics, dashboards, workflow intelligence, productivity indicators, or other derivations from the stored event data.

---

## 2. High-Level Goal

The goal is to build a reliable GitHub logging pipeline.

At a high level:

```text
GitHub Repository Activity
        ↓
GitHub Webhook
        ↓
Public Webhook URL
        ↓
Backend Webhook Endpoint
        ↓
Signature Verification
        ↓
Event Normalization
        ↓
Database Storage
        ↓
APIs / Reports / Data Consumers
```

The system should capture GitHub activity as structured metadata so that it can later be queried, analyzed, summarized, or visualized.

---

## 3. What We Mean by “GitHub Logs”

In this context, “GitHub logs” means GitHub webhook event data.

These are not server logs or Git command-line logs. They are structured HTTP payloads sent by GitHub when actions happen inside a repository.

Examples:

- Someone pushes code
- A pull request is opened
- A pull request is merged
- A pull request is closed without merge
- A review is submitted
- A review comment is added
- A GitHub Actions workflow completes
- A deployment is created
- A deployment status changes
- GitHub tests the webhook connection

Each of these actions can generate a webhook event.

---

## 4. Why Webhooks Are Used

GitHub Webhooks are useful because they send events immediately when repository activity happens.

Instead of repeatedly polling GitHub APIs, our backend receives events in near real time.

Benefits:

- Near real-time event capture
- Lower API polling overhead
- Clear event-based architecture
- Easy integration with dashboards and analytics pipelines
- Supports repository activity tracking
- Supports automation triggers
- Supports audit-style workflow logs

---

## 5. What We Can Log from GitHub

GitHub can emit many event types. For this logging system, the most useful event categories are:

| Event Category | GitHub Event | Why It Is Useful |
|---|---|---|
| Connectivity | `ping` | Confirms webhook setup is working |
| Code activity | `push` | Captures branch pushes and commit volume |
| Pull request lifecycle | `pull_request` | Captures PR opened, updated, closed, merged |
| Code review | `pull_request_review` | Captures review actions such as approval or changes requested |
| Inline review discussion | `pull_request_review_comment` | Captures review comment activity on code |
| CI/CD | `workflow_run` | Captures GitHub Actions workflow status |
| Deployment | `deployment` | Captures deployment creation |
| Deployment result | `deployment_status` | Captures deployment lifecycle status |

These events provide enough information to build repository activity timelines and downstream workflow analytics.

---

## 6. Recommended Events to Enable in GitHub

When configuring the GitHub webhook, select the following events:

| GitHub Webhook Event | Enable? | Reason |
|---|---:|---|
| Pushes | Yes | Required for commit and branch activity |
| Pull requests | Yes | Required for PR lifecycle tracking |
| Pull request reviews | Yes | Required for review participation tracking |
| Pull request review comments | Yes | Required for inline review interaction tracking |
| Workflow runs | Yes | Required for CI/CD status tracking |
| Deployments | Yes | Required for deployment tracking |
| Deployment statuses | Yes | Required for deployment outcome tracking |
| Ping | Automatic | Sent by GitHub when webhook is created/tested |

Do not select “Send me everything” unless there is a clear requirement. Selecting only required events keeps the system focused and reduces unnecessary payload volume.

---

## 7. What Data Should Be Logged

The backend should store a consistent top-level event record for every webhook delivery.

### 7.1 Common Fields for All Events

| Field | Description |
|---|---|
| `delivery_id` | Unique GitHub delivery ID from the `X-GitHub-Delivery` header |
| `source` | Event source, usually `github` |
| `event_type` | GitHub event name from `X-GitHub-Event` |
| `action` | Event action from payload, if present |
| `repository_id` | GitHub repository ID |
| `repository_name` | Short repository name |
| `repository_full_name` | Owner/repository format |
| `repository_private` | Whether repository is private |
| `actor_id` | GitHub actor ID |
| `actor_login` | GitHub username |
| `actor_type` | User, Bot, Organization, etc. |
| `is_bot` | Boolean classification for bot users |
| `occurred_at` | Best timestamp for when the GitHub activity happened |
| `received_at` | Timestamp when our backend received the webhook |
| `metadata` | Event-specific normalized metadata |
| `raw_payload` | Optional original payload, depending on storage policy |

### 7.2 Why Normalize the Data

GitHub webhook payloads are large and event-specific. Different event types have different nested structures.

Normalization gives us a consistent internal format.

Example normalized shape:

```json
{
  "id": "github-delivery-id",
  "source": "github",
  "event_type": "pull_request",
  "action": "closed",
  "repository": {
    "id": 123,
    "name": "example-repo",
    "full_name": "org/example-repo",
    "private": false
  },
  "actor": {
    "id": 456,
    "login": "octocat",
    "type": "User"
  },
  "occurred_at": "2026-05-22T06:12:49Z",
  "metadata": {}
}
```

This structure makes downstream processing easier.

---

## 8. Event-Specific Data to Capture

## 8.1 `ping`

### Meaning

GitHub sends this event to test whether the webhook endpoint is reachable.

### Capture

| Field | Description |
|---|---|
| `repository` | Repository where webhook was configured |
| `actor` | User who created or triggered the webhook |
| `hook_id` | Webhook ID, if needed |
| `zen` | GitHub test message, optional |

### Interpretation

A `ping` event proves that GitHub can reach the webhook endpoint.

It does not mean developer activity happened.

---

## 8.2 `push`

### Meaning

A commit or set of commits was pushed to a branch.

### Capture

| Field | Description |
|---|---|
| `branch` | Branch that received the push |
| `commit_count` | Number of commits in the push payload |
| `distinct_commit_count` | Number of distinct commits |
| `head_commit_id` | Latest commit SHA |
| `before` | Previous commit SHA |
| `after` | New commit SHA |
| `pusher_name` | Name of the pusher |
| `pusher_email` | Email of the pusher |
| `commit_authors` | Authors of commits in the push |
| `created` | Whether branch/tag was created |
| `deleted` | Whether branch/tag was deleted |
| `forced` | Whether this was a force push |

### Interpretation

A `push` event means GitHub received code changes on a branch.

Safe conclusions:

- A branch was updated
- One or more commits were pushed
- The latest commit SHA is known
- The pusher identity is available

Unsafe conclusions:

- The code is correct
- The feature is complete
- The push is production-ready

---

## 8.3 `pull_request`

### Meaning

A pull request lifecycle event occurred.

### Common Actions

| Action | Meaning |
|---|---|
| `opened` | PR was created |
| `closed` | PR was closed or merged |
| `reopened` | PR was reopened |
| `synchronize` | New commits were pushed to the PR branch |
| `ready_for_review` | Draft PR became ready |
| `converted_to_draft` | PR was converted to draft |
| `edited` | PR title/body/base was edited |
| `assigned` | Someone was assigned |
| `review_requested` | Review was requested |

### Capture

| Field | Description |
|---|---|
| `pr_number` | Pull request number |
| `pr_id` | GitHub PR ID |
| `pr_state` | Open or closed |
| `pr_author` | PR creator |
| `title` | Optional, if allowed by storage policy |
| `base_branch` | Target branch |
| `head_branch` | Source branch |
| `created_at` | PR creation time |
| `updated_at` | PR last update time |
| `closed_at` | PR close time |
| `merged_at` | PR merge time |
| `merged` | Boolean merge status |
| `additions` | Number of added lines |
| `deletions` | Number of deleted lines |
| `changed_files` | Number of changed files |
| `commits` | Number of commits |
| `requested_reviewers_count` | Number of requested reviewers |
| `draft` | Whether PR is draft |

### Critical Interpretation Rule

For pull requests:

```text
action = closed does not always mean merged
```

GitHub uses the `closed` action for both:

1. PR merged
2. PR closed without merge

Correct interpretation:

```text
If action = closed and merged = true:
    PR was merged

If action = closed and merged = false:
    PR was closed without merge
```

This rule is essential for any production system.

---

## 8.4 `pull_request_review`

### Meaning

A pull request review was submitted.

### Capture

| Field | Description |
|---|---|
| `pr_number` | Related PR number |
| `review_id` | GitHub review ID |
| `review_state` | Approved, commented, changes requested, etc. |
| `reviewer_login` | Reviewer username |
| `submitted_at` | Review submission timestamp |
| `commit_id` | Commit SHA reviewed, if available |

### Interpretation

This event confirms that a review action happened.

Safe conclusions:

- A review was submitted
- The review state is known
- The reviewer identity is known

Unsafe conclusions:

- The code is definitely correct
- The review was detailed
- The reviewer’s reasoning is known

---

## 8.5 `pull_request_review_comment`

### Meaning

An inline comment was added or updated on a pull request diff.

### Capture

| Field | Description |
|---|---|
| `pr_number` | Related PR number |
| `comment_id` | GitHub comment ID |
| `commenter_login` | Comment author |
| `path` | File path, if storage policy allows |
| `path_hash` | Hashed file path, if avoiding raw paths |
| `path_extension` | File extension |
| `position` | Diff position, if available |
| `created_at` | Comment creation timestamp |
| `updated_at` | Comment update timestamp |

### Interpretation

This event shows review discussion activity at code level.

If review text is not stored, the system should not claim to know what was discussed.

---

## 8.6 `workflow_run`

### Meaning

A GitHub Actions workflow run event occurred.

### Capture

| Field | Description |
|---|---|
| `workflow_id` | GitHub workflow ID |
| `workflow_name` | Workflow name |
| `run_id` | Workflow run ID |
| `run_number` | Workflow run number |
| `status` | Current status |
| `conclusion` | Final result if completed |
| `head_branch` | Branch the workflow ran on |
| `head_sha` | Commit SHA |
| `run_started_at` | Workflow start time |
| `updated_at` | Last update time |
| `duration_seconds` | Derived duration, if computable |

### Interpretation

A workflow event gives CI/CD status.

Examples:

```text
status = completed and conclusion = success
→ workflow completed successfully

status = completed and conclusion = failure
→ workflow completed with failure
```

Do not infer the detailed failure reason unless logs are separately collected.

---

## 8.7 `deployment`

### Meaning

A GitHub deployment object was created.

### Capture

| Field | Description |
|---|---|
| `deployment_id` | GitHub deployment ID |
| `environment` | Target environment |
| `creator_login` | User or bot that created deployment |
| `ref` | Branch or SHA deployed |
| `sha` | Commit SHA |
| `created_at` | Deployment creation timestamp |

### Interpretation

A deployment event means a deployment was initiated.

It does not prove deployment success.

---

## 8.8 `deployment_status`

### Meaning

A deployment status changed.

### Capture

| Field | Description |
|---|---|
| `deployment_id` | Related deployment ID |
| `environment` | Target environment |
| `state` | Deployment status |
| `creator_login` | Status creator |
| `created_at` | Status creation timestamp |
| `target_url` | Optional deployment URL |
| `environment_url` | Optional environment URL |

### Interpretation

This event is the correct source for deployment outcome.

Examples:

```text
state = success
→ deployment succeeded

state = failure
→ deployment failed
```

---

## 9. Logging Instructions

## 9.1 Backend Endpoint

Create a webhook endpoint such as:

```text
POST /webhooks/github
```

This endpoint should:

1. Read GitHub headers
2. Verify the webhook signature
3. Parse JSON body
4. Identify event type
5. Normalize event payload
6. Store the normalized record
7. Return success response

---

## 9.2 Required GitHub Headers

The backend should read these headers:

| Header | Purpose |
|---|---|
| `X-GitHub-Event` | Event type |
| `X-GitHub-Delivery` | Unique delivery ID |
| `X-Hub-Signature-256` | HMAC signature for verification |
| `User-Agent` | GitHub hookshot client information |

---

## 9.3 Signature Verification

GitHub signs webhook payloads using the webhook secret.

The backend must verify:

```text
X-Hub-Signature-256
```

Verification logic:

```pseudo
expected = "sha256=" + hmac_sha256(secret, raw_request_body)

if not constant_time_compare(expected, received_signature):
    reject request with 401
```

This prevents unauthorized systems from sending fake GitHub events.

---

## 9.4 Idempotency

GitHub can redeliver webhook events.

The backend should use `X-GitHub-Delivery` as an idempotency key.

Recommended rule:

```text
Do not store two records with the same delivery_id.
```

Recommended database constraint:

```sql
UNIQUE(delivery_id)
```

---

## 9.5 Storage Recommendation

A generic database table can look like this:

```sql
CREATE TABLE github_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    delivery_id TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    event_type TEXT NOT NULL,
    action TEXT,
    repository_id INTEGER,
    repository_name TEXT,
    repository_full_name TEXT,
    repository_private BOOLEAN,
    actor_id INTEGER,
    actor_login TEXT,
    actor_type TEXT,
    is_bot BOOLEAN,
    occurred_at TEXT,
    received_at TEXT NOT NULL,
    normalized_payload JSON NOT NULL,
    raw_payload JSON
);
```

Recommended indexes:

```sql
CREATE INDEX idx_github_events_event_type ON github_events(event_type);
CREATE INDEX idx_github_events_action ON github_events(action);
CREATE INDEX idx_github_events_repository ON github_events(repository_full_name);
CREATE INDEX idx_github_events_actor ON github_events(actor_login);
CREATE INDEX idx_github_events_occurred_at ON github_events(occurred_at);
```

---

## 9.6 Raw Payload Storage Policy

There are two possible approaches.

### Option A: Metadata-Only Storage

Store only normalized metadata.

Advantages:

- Smaller storage
- Better privacy
- Easier analytics
- Less sensitive content retained

Disadvantages:

- Cannot later inspect full GitHub payload
- Cannot extract additional fields without receiving future events

### Option B: Raw Payload + Normalized Payload

Store both raw and normalized payloads.

Advantages:

- Full reprocessing possible
- Easier debugging
- Can extract additional fields later

Disadvantages:

- Larger storage
- More sensitive data
- Requires stronger access controls and retention policy

Recommended default:

```text
Store normalized metadata only unless raw payload retention is explicitly required.
```

---

## 10. ngrok Setup for Local Testing

ngrok is used only to expose the local backend to GitHub during development or POC testing.

GitHub cannot send webhooks to `localhost`, so ngrok provides a temporary public HTTPS URL.

---

## 10.1 Install ngrok

Check installation:

```bash
ngrok version
```

If not installed on Ubuntu/Debian using snap:

```bash
sudo snap install ngrok
```

Alternatively, install from the official ngrok dashboard.

---

## 10.2 Authenticate ngrok

Create or sign into an ngrok account.

Get the auth token from the ngrok dashboard.

Configure it:

```bash
ngrok config add-authtoken <YOUR_NGROK_AUTH_TOKEN>
```

---

## 10.3 Run Local Backend

Start the backend service.

Example:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify health:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{"status":"ok"}
```

---

## 10.4 Start ngrok Tunnel

Run:

```bash
ngrok http 8000
```

ngrok will show a public forwarding URL similar to:

```text
https://example-name.ngrok-free.app
```

The GitHub webhook endpoint becomes:

```text
https://example-name.ngrok-free.app/webhooks/github
```

Important:

```text
If ngrok restarts, the URL may change.
If the URL changes, update the GitHub webhook configuration.
```

---

## 11. GitHub Webhook Setup Instructions

## 11.1 Open Repository Settings

Go to the GitHub repository.

Then open:

```text
Settings → Webhooks → Add webhook
```

---

## 11.2 Configure Payload URL

Use the backend URL.

For local POC using ngrok:

```text
https://<ngrok-domain>/webhooks/github
```

For deployed environments:

```text
https://<api-domain>/webhooks/github
```

---

## 11.3 Configure Content Type

Select:

```text
application/json
```

---

## 11.4 Configure Secret

Set a strong shared secret.

Example generation command:

```bash
openssl rand -hex 32
```

The same secret must be configured in:

1. GitHub webhook settings
2. Backend environment variable

Example backend environment variable:

```env
GITHUB_WEBHOOK_SECRET=<same-secret-used-in-github>
```

If the values do not match, signature verification should fail.

---

## 11.5 Select Events

Choose:

```text
Let me select individual events
```

Enable:

- Pushes
- Pull requests
- Pull request reviews
- Pull request review comments
- Workflow runs
- Deployments
- Deployment statuses

Keep the webhook active.

Save the webhook.

---

## 11.6 Verify Ping Event

After saving the webhook, GitHub sends a `ping` event.

The backend should receive and store it.

Verification options:

1. Check application logs
2. Check database
3. Call events API
4. Check GitHub webhook recent deliveries

Example:

```bash
curl -s http://127.0.0.1:8000/events | python3 -m json.tool
```

Expected result:

```text
At least one event with event_type = ping
```

---

## 12. Testing the Logging Flow

Use the following actions to confirm each event type.

| Test Action | Expected GitHub Event |
|---|---|
| Create or test webhook | `ping` |
| Push commit to branch | `push` |
| Open pull request | `pull_request` with `opened` |
| Push more commits to PR branch | `push` and often `pull_request` with `synchronize` |
| Submit PR review | `pull_request_review` |
| Add inline review comment | `pull_request_review_comment` |
| Merge pull request | `pull_request` with `closed` and `merged = true` |
| Close PR without merge | `pull_request` with `closed` and `merged = false` |
| Run GitHub Actions workflow | `workflow_run` |
| Create deployment | `deployment` |
| Update deployment status | `deployment_status` |

---

## 13. How to Interpret Stored Logs

## 13.1 General Interpretation Flow

When reading any stored event:

1. Check `event_type`
2. Check `action`
3. Check `repository_full_name`
4. Check `actor_login`
5. Check `occurred_at`
6. Check event-specific metadata
7. Apply event-specific interpretation rules

---

## 13.2 Pull Request Interpretation

Most important rule:

```text
Do not interpret pull_request.closed as merged unless metadata.merged is true.
```

Examples:

```text
event_type = pull_request
action = closed
metadata.merged = true

Interpretation:
PR was merged.
```

```text
event_type = pull_request
action = closed
metadata.merged = false

Interpretation:
PR was closed without merge.
```

---

## 13.3 Push Interpretation

Example:

```text
event_type = push
metadata.branch = feature/login
metadata.commit_count = 3
```

Interpretation:

```text
Three commits were pushed to feature/login.
```

Do not interpret this as:

```text
Three features were completed.
```

---

## 13.4 Workflow Interpretation

Example:

```text
event_type = workflow_run
metadata.status = completed
metadata.conclusion = success
```

Interpretation:

```text
The workflow completed successfully.
```

Example:

```text
event_type = workflow_run
metadata.status = completed
metadata.conclusion = failure
```

Interpretation:

```text
The workflow completed with failure.
```

Do not infer the failure reason unless workflow logs are separately captured.

---

## 13.5 Deployment Interpretation

Use `deployment` and `deployment_status` together.

```text
deployment
→ deployment was initiated

deployment_status with state = success
→ deployment succeeded

deployment_status with state = failure
→ deployment failed
```

---

## 14. Data Available for Future Derivations

Once logs are stored, downstream systems can derive metrics such as:

| Derivation | Required Events |
|---|---|
| Repository activity volume | `push`, `pull_request` |
| PR open count | `pull_request.opened` |
| PR merge count | `pull_request.closed` + `merged = true` |
| PR close-without-merge count | `pull_request.closed` + `merged = false` |
| Average PR size | `pull_request` metadata additions/deletions/files |
| Review participation | `pull_request_review` |
| Inline review activity | `pull_request_review_comment` |
| CI success/failure rate | `workflow_run` |
| Deployment frequency | `deployment` |
| Deployment success rate | `deployment_status` |
| Human vs bot activity | `actor_type`, `is_bot` |
| Branch activity | `push.metadata.branch` |
| Lead time approximation | PR created/merged timestamps |

These derivations are separate from ingestion. The ingestion layer only needs to reliably collect and store the necessary fields.

---

## 15. Minimum Viable Logging Scope

For the first production-ready version, the system should at least support:

| Area | Minimum Requirement |
|---|---|
| Webhook endpoint | `POST /webhooks/github` |
| Security | Verify `X-Hub-Signature-256` |
| Idempotency | Deduplicate by `X-GitHub-Delivery` |
| Events | `ping`, `push`, `pull_request` |
| Storage | Common event fields + normalized metadata |
| API | `GET /events`, `GET /metrics/summary` |
| Reports | Export JSON event logs and summary |
| Observability | Application logs for received/rejected events |

Recommended next event support:

- `pull_request_review`
- `pull_request_review_comment`
- `workflow_run`
- `deployment`
- `deployment_status`

---

## 16. Recommended API Endpoints

## 16.1 Health Check

```text
GET /health
```

Purpose:

```text
Confirm service is running.
```

Example response:

```json
{
  "status": "ok"
}
```

---

## 16.2 Webhook Receiver

```text
POST /webhooks/github
```

Purpose:

```text
Receive GitHub webhook deliveries.
```

Expected response:

```json
{
  "status": "accepted"
}
```

---

## 16.3 Events API

```text
GET /events
```

Purpose:

```text
Return stored webhook events.
```

Optional filters for production:

```text
GET /events?repository=org/repo
GET /events?event_type=pull_request
GET /events?actor=octocat
GET /events?from=2026-01-01&to=2026-01-31
```

---

## 16.4 Summary API

```text
GET /metrics/summary
```

Purpose:

```text
Return aggregate counts.
```

Example metrics:

```json
{
  "total_events": 100,
  "events_by_type": {
    "push": 40,
    "pull_request": 30,
    "workflow_run": 20,
    "ping": 10
  },
  "events_by_repository": {
    "org/repo": 100
  },
  "bot_events": 15,
  "human_events": 85,
  "pull_requests_opened": 12,
  "pull_requests_merged": 9,
  "pushes": 40,
  "workflow_runs_completed": 20
}
```

---

## 17. Reports to Generate

The logging system should be able to export:

```text
reports/events.json
reports/summary.json
```

### `events.json`

Contains stored webhook events.

Used for:

- audit
- debugging
- dashboard input
- offline analysis
- senior review/demo

### `summary.json`

Contains aggregate counts.

Used for:

- dashboard cards
- metrics overview
- proof that events are being captured

---

## 18. Application Logging Recommendations

In addition to storing webhook data, the backend service should log operational messages.

Recommended application logs:

| Log Case | Level | Message |
|---|---|---|
| Webhook received | INFO | Event type and delivery ID |
| Signature verification failed | WARN | Delivery rejected |
| Unsupported event type | INFO/WARN | Event skipped or minimally stored |
| Event normalized | INFO | Event normalized successfully |
| Event stored | INFO | Database insert successful |
| Duplicate delivery | INFO | Duplicate ignored |
| Storage failure | ERROR | Database exception |
| JSON parse failure | WARN | Invalid payload |
| Missing required header | WARN | Request rejected |

Example log lines:

```text
INFO received github webhook delivery_id=abc event_type=pull_request
INFO normalized event delivery_id=abc event_type=pull_request action=opened
INFO stored github event delivery_id=abc repository=org/repo
WARN invalid github signature delivery_id=abc
INFO duplicate github delivery ignored delivery_id=abc
```

---

## 19. Error Handling

| Scenario | Expected Behavior |
|---|---|
| Missing signature | Return `401` |
| Invalid signature | Return `401` |
| Missing event header | Return `400` |
| Invalid JSON | Return `400` |
| Unsupported event | Store minimal record or return accepted based on policy |
| Duplicate delivery | Return `200`, do not duplicate |
| Database error | Return `500`, log error |

Recommended approach for unsupported events:

```text
Store a minimal normalized record if the event is valid and signed.
```

This allows future support without losing visibility.

---

## 20. Security Considerations

- Always verify GitHub webhook signatures.
- Do not expose webhook endpoint without signature validation.
- Store secrets in environment variables, not code.
- Restrict database access.
- Avoid storing raw payloads unless required.
- If raw payloads are stored, define retention and access policies.
- Avoid logging sensitive payload contents in application logs.
- Use HTTPS for public webhook endpoints.
- Rotate webhook secrets when needed.

---

## 21. Production Deployment Considerations

For production, ngrok should not be used.

Use a stable HTTPS endpoint such as:

```text
https://api.company.com/webhooks/github
```

Recommended production setup:

```text
GitHub
  ↓
Load Balancer / API Gateway
  ↓
Webhook Service
  ↓
Queue
  ↓
Worker / Normalizer
  ↓
Database / Data Warehouse
```

For a small deployment, direct API-to-database storage is acceptable.

For higher reliability, use a queue between receiving and processing.

Benefits of queue-based design:

- Faster webhook acknowledgment
- Better retry handling
- More resilient processing
- Reduced chance of GitHub delivery timeout
- Scalable event processing

---

## 22. Recommended Production Architecture

```text
GitHub Webhook
    ↓
HTTPS Endpoint
    ↓
Signature Verification
    ↓
Store Raw/Minimal Delivery Record
    ↓
Queue Event
    ↓
Normalize Event
    ↓
Store Normalized Metadata
    ↓
Expose APIs / Send to Analytics
```

This separates ingestion from processing and makes the system more reliable.

---

## 23. Validation Checklist

Before submitting or demoing the logging system, verify:

- [ ] Backend service starts successfully
- [ ] `/health` returns `{"status":"ok"}`
- [ ] ngrok or public HTTPS URL is active
- [ ] GitHub webhook payload URL is correct
- [ ] GitHub webhook secret matches backend secret
- [ ] Content type is `application/json`
- [ ] Required GitHub events are selected
- [ ] GitHub `ping` event is received
- [ ] Push event is received after pushing code
- [ ] PR opened event is received after opening PR
- [ ] PR closed/merged behavior is interpreted using `metadata.merged`
- [ ] Events are stored in database
- [ ] `/events` returns stored events
- [ ] `/metrics/summary` returns aggregate metrics
- [ ] Duplicate deliveries are not double-counted
- [ ] Invalid signatures are rejected

---

## 24. Handover Summary for Seniors

This implementation is responsible for bringing GitHub activity data into our system.

It captures GitHub webhook events, verifies that the requests are genuinely from GitHub, normalizes the important metadata, and stores the logs in a structured format.

The ingestion layer does not need to decide productivity, quality, or business value. Its responsibility is to reliably collect clean event data.

Downstream systems can later use this data to build:

- repository activity timelines
- pull request analytics
- review participation metrics
- CI/CD success and failure reports
- deployment frequency and status reporting
- human versus bot activity summaries
- engineering workflow dashboards

The most important implementation rule is that GitHub pull request close events must be interpreted carefully:

```text
pull_request.closed + merged = true
→ PR merged

pull_request.closed + merged = false
→ PR closed without merge
```

This distinction is essential for accurate analytics and automation.

---

## 25. Final Scope Statement

This document covers the process up to data availability.

Completed scope:

```text
GitHub event happens
→ GitHub sends webhook
→ Backend receives webhook
→ Backend verifies signature
→ Backend normalizes event
→ Backend stores event metadata
→ API/report exposes collected data
```

Not covered in this scope:

```text
Advanced analytics
Developer scoring
AI-based interpretation
Code quality assessment
Business productivity measurement
Dashboard design beyond basic reports
```

The output of this logging layer is clean GitHub event metadata that can be safely used by future analytics or intelligence systems.