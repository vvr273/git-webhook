# GitHub Webhook Scope and Possibilities

## Purpose

This document explains the scope of the current GitHub webhook setup and what is possible if we want to expand it.

The main question it answers is:

- Is this current setup repository-specific?
- Is it user-specific?
- Can it cover all repositories?
- Can it cover all users?
- Can it cover all branches?

Short answer:

- the current setup is repository-specific
- it is not user-specific in the identity-provider sense
- it can capture activity from any user who acts inside that configured repository
- it can capture activity from all branches that generate supported webhook events in that configured repository
- to cover many repositories, we need to configure many webhook sources or move to a broader GitHub integration model

## What the Current Setup Is

The current POC uses:

- one FastAPI webhook receiver
- one public ngrok URL
- one GitHub webhook configured on a repository

That means the current data source is:

- repository webhook based

In the current POC, when the webhook is configured on:

```text
vvr273/git-webhook
```

the service receives events only from that repository.

## Is the Current Setup Repository-Specific?

Yes.

The current setup is repository-specific.

Why:

- GitHub repository webhooks are attached to a specific repository
- GitHub sends events only for that repository
- the payload includes the repository name in every event

So if the webhook is configured on:

```text
vvr273/git-webhook
```

then pushes, PRs, reviews, workflow runs, and deployments from that repository can be captured.

But activity in a different repository will not be sent unless that other repository also has a webhook pointing to the same service.

## Is the Current Setup User-Specific?

No, not in the sense of “track one user across all GitHub”.

This setup does not attach to a user account globally.

Instead, it listens for repository events.

However, user identity is still present inside those repository events.

That means:

- if user `alice` pushes to the repository, the event shows `alice`
- if user `bob` opens a PR in the repository, the event shows `bob`
- if `github-actions[bot]` runs a workflow, the event shows that bot actor

So the right interpretation is:

- not user-scoped collection
- but user-attributed events inside the configured repository

## Can It Capture All Users in a Repository?

Yes.

If many people contribute to the same repository, the webhook can capture supported events for all of them, as long as:

- the action happens in that repository
- GitHub emits one of the supported webhook events
- the webhook is configured correctly
- the receiving service is reachable

Examples of contributors whose activity can appear:

- repository owner
- collaborators
- organization members
- outside contributors opening PRs
- bots such as Dependabot or GitHub Actions

## Can It Capture All Branches in a Repository?

Yes, in the webhook-event sense.

If activity on a branch creates a supported GitHub event, the service can capture it.

Examples:

- push to `main` -> `push`
- push to `feature/api-cleanup` -> `push`
- push more commits to a PR branch -> `push`, and often `pull_request` with `synchronize`
- delete a branch through push mechanics -> still part of `push` metadata if GitHub emits it

Important clarification:

- the system does not separately “discover all branches”
- it only sees branches when GitHub sends an event involving them

So this is event-driven branch visibility, not full branch inventory.

## Can It Capture All Repositories for One User?

Not with the current repository-webhook setup alone.

If one user works in 20 repositories, a single repository webhook only shows activity in the one repository where it is installed.

To cover all repositories for one user, one of these would be needed:

### Option 1: Add the same webhook to every repository

This is the simplest extension of the current design.

How it works:

- configure the same webhook URL and secret on multiple repositories
- all those repositories send events to the same FastAPI service
- the service stores them together
- `repository_full_name` distinguishes them

Result:

- multi-repository event ingestion
- still webhook-based
- still easy to reason about

Limitation:

- setup effort increases with repository count

### Option 2: Use GitHub organization webhooks

If the repositories are under a GitHub organization, GitHub organization-level webhooks may help for some event classes.

Result:

- broader scope than one repository

Limitation:

- behavior and available events depend on GitHub’s org webhook model
- still not equivalent to complete user-centric activity tracking everywhere

### Option 3: Use a GitHub App

This is the most scalable long-term approach.

A GitHub App can be installed on:

- selected repositories
- all repositories in an organization

Result:

- centralized event collection
- better permission control
- easier expansion across many repositories
- more production-appropriate than manual per-repo webhook setup

For a real Developer Intelligence platform, this is usually the better long-term direction.

## Can It Capture All Repositories for All Users in an Organization?

Yes, but not with just the current one-repo webhook.

Possible approaches:

### Approach A: Same webhook on many repositories

If every relevant repository points to the same service:

- repository A sends events
- repository B sends events
- repository C sends events

and so on.

The database then becomes a cross-repository event store.

### Approach B: GitHub App installed across the organization

This is the better long-term architecture.

Why:

- cleaner rollout
- centralized permissions
- easier scaling
- easier governance
- better fit for enterprise environments

## What “All Users” Really Means

This needs careful wording.

There are two very different meanings:

### Meaning 1: All users who act inside tracked repositories

This is possible.

If a tracked repository has activity from many people, the webhook data can include all of them.

### Meaning 2: Everything a GitHub user does everywhere on GitHub

This is not what repository webhooks provide.

Repository webhooks do not give a universal user activity stream across all repos unless those repos are also integrated.

So if the question is:

- “Can we measure all activity of user X across GitHub?”

the answer is:

- not from one repository webhook

## What About Branch Creation?

Branch creation is not usually stored as a separate first-class “branch created” event in this POC.

But branch creation can still appear indirectly.

Example:

- create branch locally
- push branch to GitHub
- GitHub sends `push`

From that `push`, we can infer:

- a branch exists
- activity happened on that branch

If we enrich our `push` normalization to preserve fields like:

- `created`
- `deleted`
- `forced`

then we can describe branch lifecycle more clearly.

So the answer is:

- yes, branch activity can be tracked
- yes, branch creation can often be inferred from push metadata
- no, this POC is not currently a full branch inventory service

## What About Measuring “All Branches” Over Time?

Possible, with conditions.

If every branch eventually emits events, then over time the database can accumulate branch-level activity history.

This means we can later answer questions like:

- which branches had pushes
- which branches were used in PRs
- which branches had workflow activity

But this is still event-driven visibility, not a Git reference crawler.

If full branch inventory is needed, an additional GitHub API sync layer would help.

## What This POC Is Best At

The current architecture is best at:

- repository activity logging
- branch activity logging through push and PR events
- contributor activity logging within tracked repositories
- PR lifecycle tracking
- review participation tracking
- workflow activity tracking
- deployment activity tracking

## What It Is Not Yet

The current POC is not yet:

- a complete cross-GitHub user activity tracker
- a complete organization-wide telemetry platform
- a full branch inventory system
- a full repository discovery system
- a global GitHub graph analytics system

Those are possible future directions, but they require broader integration.

## Recommended Future Scopes

## Scope 1: Single Repository POC

Best for:

- proving ingestion works
- proving normalization works
- proving dashboards and summaries work

Current status:

- already achieved

## Scope 2: Multi-Repository Webhook Aggregation

Best for:

- testing cross-repo analytics quickly
- comparing activity across repositories
- minimal architecture change

How:

- point multiple repository webhooks to the same FastAPI service

Recommended DB addition:

- keep indexing by `repository_full_name`

## Scope 3: Organization-Scale GitHub App

Best for:

- production rollout
- enterprise governance
- broad repository coverage
- easier lifecycle management

How:

- move from per-repo webhook setup to GitHub App installation

## Practical Answers to Common Questions

### “Can this track all users in this repo?”

Yes.

### “Can this track all branches in this repo?”

Yes, if those branches generate supported webhook events.

### “Can this track all repos for this user automatically?”

No, not with one repo webhook alone.

### “Can this track many repos if we configure them all?”

Yes.

### “Can this become org-wide?”

Yes, preferably through a GitHub App or broader integration model.

### “Can this become a full Developer Intelligence ingestion layer?”

Yes, this POC is a valid starting point for that direction.

## Recommended Conclusion

The current POC should be described as:

- repository-scoped event ingestion
- with user-attributed and branch-attributed metadata
- expandable to multi-repository ingestion
- and a strong candidate to evolve into an organization-wide GitHub App based ingestion model

That is the most accurate and defensible description.
