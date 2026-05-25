# GitHub Webhook Response Interpretation Guide

## Purpose

This document explains what each stored webhook response means in plain language.

The goal is not just to list event types, but to interpret them clearly:
- what action happened in GitHub
- what the stored response is telling us
- what fields matter most
- what conclusions are safe to draw
- what conclusions should not be drawn

This document should be used when reading:
- `GET /events`
- `GET /metrics/summary`
- `reports/events.json`
- `reports/summary.json`
- the HTML dashboard

## Important Principle

This system stores GitHub webhook metadata, not the full human story.

That means:
- it tells us what GitHub event happened
- it tells us when it happened
- it tells us who triggered it
- it tells us which repository it affected
- it may tell us counts and status fields

It does not tell us:
- why the person made the change
- what exact code changed
- whether the code quality was good or bad
- the full written content of PRs, comments, or reviews

So this data is best used for:
- workflow tracking
- activity measurement
- automation tracking
- event timelines

It should not be over-interpreted as proof of intent or quality.

## Basic Event Structure

Each stored event has fields like:

```json
{
  "delivery_id": "...",
  "event_type": "...",
  "action": "...",
  "repository_full_name": "...",
  "actor_login": "...",
  "occurred_at": "...",
  "normalized_payload": {
    "metadata": {}
  }
}
```

How to read them:

- `delivery_id`
  GitHub’s unique id for this webhook delivery

- `event_type`
  the category of GitHub event, such as `push` or `pull_request`

- `action`
  the sub-action if GitHub provided one, such as `opened` or `closed`

- `repository_full_name`
  which repository the event belongs to

- `actor_login`
  who triggered the event from GitHub’s point of view

- `occurred_at`
  best timestamp for when the activity happened

- `normalized_payload.metadata`
  the event-specific details

## How To Interpret Each Event Type

## 1. `ping`

### What it means

This is GitHub testing the webhook connection.

### What action caused it

Usually:
- a webhook was added in GitHub
- or GitHub sent a test ping

### What it tells us

- the webhook exists
- GitHub attempted delivery
- if stored successfully, the service accepted it

### What it does not tell us

- no developer work happened
- no code change happened
- no PR activity happened

### Safe interpretation

`ping` proves connectivity, not engineering activity.

## 2. `push`

### What it means

A push was made to GitHub.

### What action caused it

Examples:
- pushing a branch for the first time
- pushing commits to an existing branch
- pushing commits after making local changes

### Important metadata

Look at:
- `metadata.branch`
- `metadata.commit_count`
- `metadata.distinct_commit_count`
- `metadata.head_commit_id`
- `metadata.pusher_name`
- `metadata.pusher_email`
- `metadata.commit_authors`

### What it tells us

- which branch received the push
- how many commits were included in that push
- who pushed it
- who authored the included commits, where available

### What it does not tell us

- it does not show commit messages
- it does not show changed files
- it does not show code content
- it does not tell us if the push was “good” or “bad”

### Safe interpretation

A `push` event tells us that repository activity happened and gives basic volume information.

### Example interpretation

If:
- `branch = feature/test`
- `commit_count = 3`

Then we can safely say:
- three commits were pushed to the `feature/test` branch

We should not say:
- three useful features were completed

## 3. `pull_request`

### What it means

A PR lifecycle event happened.

### What action caused it

Examples:
- PR opened
- PR updated
- PR reopened
- PR closed
- PR merged

### Important metadata

Look at:
- `action`
- `metadata.pr_number`
- `metadata.pr_state`
- `metadata.pr_author`
- `metadata.base_branch`
- `metadata.head_branch`
- `metadata.merged`
- `metadata.created_at`
- `metadata.updated_at`
- `metadata.closed_at`
- `metadata.merged_at`
- `metadata.requested_reviewers_count`

### Key interpretation rule

For PRs, `action = closed` does not automatically mean merged.

You must also check:
- `metadata.merged`

Interpretation:
- `action = opened` means PR was created
- `action = synchronize` usually means new commits were pushed to the PR branch
- `action = reopened` means PR was reopened
- `action = closed` and `metadata.merged = true` means PR was merged
- `action = closed` and `metadata.merged = false` means PR was closed without merge

### What it tells us

- PR lifecycle state
- who opened the PR
- source branch and target branch
- rough PR size indicators such as additions, deletions, changed files, and commits

### What it does not tell us

- it does not store the PR title
- it does not store the PR body
- it does not store the diff
- it does not tell us whether the PR content was good

### Safe interpretation

A `pull_request` event tells us PR workflow movement, not code quality or business value.

### Example interpretation

If:
- `event_type = pull_request`
- `action = closed`
- `metadata.merged = true`

Then we can clearly say:
- the PR was merged

If:
- `event_type = pull_request`
- `action = closed`
- `metadata.merged = false`

Then we can clearly say:
- the PR was closed without being merged

## 4. `pull_request_review`

### What it means

A PR review was submitted.

### What action caused it

Examples:
- approve
- comment review
- request changes

### Important metadata

Look at:
- `metadata.pr_number`
- `metadata.review_id`
- `metadata.review_state`
- `metadata.submitted_at`
- `metadata.reviewer_login`

### What it tells us

- a reviewer took a review action on the PR
- which PR the review belonged to
- what kind of review state GitHub recorded

### What it does not tell us

- it does not store the review body text
- it does not explain why approval or rejection happened

### Safe interpretation

A `pull_request_review` event proves review participation, not the content of the review.

### Example interpretation

If:
- `review_state = approved`

Then we can say:
- a reviewer approved the PR

We should not say:
- the code is definitely correct

## 5. `pull_request_review_comment`

### What it means

An inline PR review comment event happened.

### What action caused it

Usually:
- someone commented on a file/line in a PR review context

### Important metadata

Look at:
- `metadata.pr_number`
- `metadata.comment_id`
- `metadata.commenter_login`
- `metadata.path_hash`
- `metadata.path_extension`
- `metadata.created_at`
- `metadata.updated_at`

### What it tells us

- a detailed code-review-style comment happened
- it was tied to a PR
- the commenter identity is available
- a hashed path or file extension is available without exposing file content

### What it does not tell us

- it does not store the comment body
- it does not tell us what exact file content was discussed

### Safe interpretation

A `pull_request_review_comment` event is a signal of detailed review interaction, not stored review content.

## 6. `workflow_run`

### What it means

A GitHub Actions workflow run event happened.

### What action caused it

Examples:
- workflow started
- workflow completed
- workflow updated during execution

### Important metadata

Look at:
- `metadata.workflow_id`
- `metadata.workflow_name`
- `metadata.run_id`
- `metadata.run_number`
- `metadata.status`
- `metadata.conclusion`
- `metadata.run_started_at`
- `metadata.duration_seconds`
- `metadata.head_branch`
- `metadata.head_sha`

### What it tells us

- CI/CD or automation activity happened
- which workflow ran
- which branch or SHA it ran against
- whether it completed
- whether it concluded successfully or not

### What it does not tell us

- it does not store logs
- it does not store build output
- it does not explain the failure cause in detail

### Safe interpretation

A `workflow_run` event is an operational automation signal.

### Example interpretation

If:
- `status = completed`
- `conclusion = success`

Then we can say:
- the workflow completed successfully

If:
- `status = completed`
- `conclusion = failure`

Then we can say:
- the workflow completed with failure

We should not say:
- the exact technical cause of the failure is known from this data alone

## 7. `deployment`

### What it means

A deployment object was created in GitHub.

### Important metadata

Look at:
- `metadata.deployment_id`
- `metadata.environment`
- `metadata.state`
- `metadata.creator_login`

### What it tells us

- a deployment-related operation was initiated
- the target environment is known if GitHub sent it

### What it does not tell us

- whether the deployment completed successfully

### Safe interpretation

`deployment` signals intent or creation of a deployment step, not completion.

## 8. `deployment_status`

### What it means

A deployment status changed.

### Important metadata

Look at:
- `metadata.deployment_id`
- `metadata.environment`
- `metadata.status`
- `metadata.creator_login`

### What it tells us

- the deployment lifecycle moved to a new state

### Safe interpretation

`deployment_status` is the better event for understanding deployment outcome.

## How To Read Common PR Cases Correctly

## Case 1: PR Opened

Look for:
- `event_type = pull_request`
- `action = opened`

Meaning:
- a new PR was created

## Case 2: PR Updated With New Commits

Look for:
- `event_type = push`
- branch matches the PR branch

And often:
- `event_type = pull_request`
- `action = synchronize`

Meaning:
- new commits were added to the PR branch

## Case 3: PR Reviewed

Look for:
- `event_type = pull_request_review`

Meaning:
- someone completed a review action

## Case 4: PR Merged

Look for:
- `event_type = pull_request`
- `action = closed`
- `metadata.merged = true`

Meaning:
- PR was merged

## Case 5: PR Closed Without Merge

Look for:
- `event_type = pull_request`
- `action = closed`
- `metadata.merged = false`

Meaning:
- PR was closed but not merged

## How To Read Summary Metrics Correctly

`/metrics/summary` is not the event log.

It is a rolled-up summary of counts.

### `total_events`

Meaning:
- total stored webhook records

### `events_by_type`

Meaning:
- how many stored records exist for each event type

Example:
- `"push": 5` means five push events were stored

### `events_by_repository`

Meaning:
- how many stored records belong to each repository

### `bot_events`

Meaning:
- number of stored events classified as bot activity

### `human_events`

Meaning:
- number of stored events classified as human activity

### `pull_requests_opened`

Meaning:
- count of `pull_request` events where action was `opened`

### `pull_requests_merged`

Meaning:
- count of PR close events where `merged = true`

### `pushes`

Meaning:
- count of `push` events

### `workflow_runs_completed`

Meaning:
- count of `workflow_run` events where a conclusion exists

## What You Can Safely Say in a Demo

Good statements:

- “We captured two push events for this repository.”
- “We can distinguish merged PRs from closed-without-merge PRs using the merged flag.”
- “We can measure review participation without storing review text.”
- “We can track workflow completion status and duration from metadata.”
- “We store metadata only, not code or diff content.”

Avoid statements like:

- “This proves the developer was productive.”
- “This proves the code was correct.”
- “This shows what exact changes were made.”
- “This proves AI wrote the code.”

Those conclusions would require additional context beyond webhook metadata.

## Recommended Reading Order When Inspecting Data

When reading an event record:

1. Check `event_type`
2. Check `action`
3. Check `repository_full_name`
4. Check `actor_login`
5. Check `occurred_at`
6. Check `normalized_payload.metadata`
7. For PR close events, always check `metadata.merged`

## Practical Examples

## Example A: Push

If you see:

```json
{
  "event_type": "push",
  "repository_full_name": "vvr273/git-webhook",
  "normalized_payload": {
    "metadata": {
      "branch": "master",
      "commit_count": 2
    }
  }
}
```

Interpretation:
- two commits were pushed to the `master` branch of `vvr273/git-webhook`

## Example B: Merged PR

If you see:

```json
{
  "event_type": "pull_request",
  "action": "closed",
  "normalized_payload": {
    "metadata": {
      "pr_number": 7,
      "merged": true
    }
  }
}
```

Interpretation:
- PR number 7 was merged

## Example C: Closed Without Merge

If you see:

```json
{
  "event_type": "pull_request",
  "action": "closed",
  "normalized_payload": {
    "metadata": {
      "pr_number": 7,
      "merged": false
    }
  }
}
```

Interpretation:
- PR number 7 was closed without merge

## Example D: Review Approved

If you see:

```json
{
  "event_type": "pull_request_review",
  "normalized_payload": {
    "metadata": {
      "review_state": "approved"
    }
  }
}
```

Interpretation:
- a reviewer approved the PR

## Example E: Workflow Success

If you see:

```json
{
  "event_type": "workflow_run",
  "normalized_payload": {
    "metadata": {
      "status": "completed",
      "conclusion": "success"
    }
  }
}
```

Interpretation:
- the workflow completed successfully

## Final Rule

Read webhook data as workflow evidence, not as full engineering truth.

This system is excellent for:
- timelines
- counts
- participation
- automation signals
- repository activity summaries

This system is intentionally limited for:
- content analysis
- code review substance
- commit intent
- code quality judgment
