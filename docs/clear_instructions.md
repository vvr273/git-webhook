# Clear Instructions: GitHub Webhook Testing Service Setup

## Who This Is For

This guide is written for someone who may be new to local setup, terminals, Git, GitHub, Python virtual environments, and ngrok.

If you follow the steps in order, you will be able to:
- run the webhook service locally
- expose it to GitHub using ngrok
- configure a GitHub webhook
- trigger events from GitHub
- view the saved event data locally

## What You Are Setting Up

You are setting up a local FastAPI service that listens for GitHub webhook events.

When actions happen in GitHub, such as:
- push
- pull request
- review
- workflow run

GitHub sends webhook requests to your local service through ngrok.

The service verifies the request, normalizes the metadata, and stores it in a local SQLite database.

## What You Need Before Starting

You need:
- a computer with terminal access
- Python 3.11 or later
- Git installed
- a GitHub account
- access to the GitHub repository where you will add the webhook
- ngrok account
- internet connection

## Folder Used in This Guide

This guide assumes the project is here:

```text
/home/think41/vishnu/roi/git-webhook
```

If your project is in a different folder, replace the path in the commands.

## Step 1: Open the Project Folder in Terminal

Open a terminal and run:

```bash
cd /home/think41/vishnu/roi/git-webhook
```

To confirm you are in the correct folder, run:

```bash
pwd
ls
```

You should see files such as:
- `pyproject.toml`
- `README.md`
- `app/`
- `tests/`

## Step 2: Check Python

Check if Python is installed:

```bash
python3 --version
```

If Python is installed, you should see a version like:

```text
Python 3.11.x
```

If Python is not installed, install it first.

### Ubuntu or Debian

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

Then verify again:

```bash
python3 --version
```

## Step 3: Create a Python Virtual Environment

A virtual environment keeps project dependencies separate from the rest of your computer.

From the project folder, run:

```bash
python3 -m venv .venv
```

Activate it:

```bash
. .venv/bin/activate
```

After activation, your terminal usually shows `(.venv)` at the beginning.

## Step 4: Install Project Dependencies

With the virtual environment active, run:

```bash
pip install -e ".[dev]"
```

This installs:
- FastAPI
- Uvicorn
- SQLAlchemy
- test dependencies
- everything needed by this project

## Step 5: Create the Environment File

Create `.env` from the example file:

```bash
cp .env.example .env
```

Open `.env` in a text editor and set the webhook secret.

Example:

```env
GITHUB_WEBHOOK_SECRET=my-super-secret-value
DATABASE_URL=sqlite:///./github_webhooks.db
STORE_RAW_PAYLOAD=false
LOG_LEVEL=INFO
```

## Step 6: Generate a Strong Secret

The webhook secret is a shared secret between GitHub and your local app.

Generate one with:

```bash
openssl rand -hex 32
```

Copy that output and paste it into `.env` after `GITHUB_WEBHOOK_SECRET=`.

Important:
- keep this value private
- you must use this exact same value later in GitHub webhook settings

## Step 7: Check Git Installation

Run:

```bash
git --version
```

If Git is not installed:

### Ubuntu or Debian

```bash
sudo apt update
sudo apt install git
```

Then check again:

```bash
git --version
```

## Step 8: Connect Git to GitHub on Your Computer

This step is only needed if you want to commit and push code from your local machine.

Check your Git identity:

```bash
git config --global user.name
git config --global user.email
```

If they are empty, set them:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

If GitHub asks for authentication during push, use one of these:
- GitHub CLI login
- Personal Access Token
- existing credential manager already configured on your machine

## Step 9: Start the Webhook Service

From the project folder, with virtual environment active, run:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Leave this terminal running.

This is your local API server.

## Step 10: Verify the Service Is Running

Open a second terminal.

Go to the project folder:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
```

Run:

```bash
curl http://127.0.0.1:8000/health
```

Expected result:

```json
{"status":"ok"}
```

If you get connection errors, the app is not running. Go back to the first terminal and start it again.

## Step 11: Install ngrok

Check whether ngrok is installed:

```bash
ngrok version
```

If it is not installed, on Ubuntu or Debian you can install it with:

```bash
sudo snap install ngrok
```

After installation, check again:

```bash
ngrok version
```

## Step 12: Create an ngrok Account in the Browser

Open this page in your browser:

```text
https://dashboard.ngrok.com/
```

Create an account or sign in.

Then open:

```text
https://dashboard.ngrok.com/get-started/your-authtoken
```

Copy the authtoken shown on that page.

## Step 13: Add the ngrok Authtoken in Terminal

Run this command and replace the placeholder with your real token:

```bash
ngrok config add-authtoken YOUR_REAL_NGROK_TOKEN
```

This only needs to be done once on your computer.

## Step 14: Start ngrok

In a new terminal, run:

```bash
ngrok http 8000
```

Leave this terminal running.

You will see output like this:

```text
Forwarding  https://example.ngrok-free.app -> http://localhost:8000
```

Copy the HTTPS URL.

You will use it like this:

```text
https://example.ngrok-free.app/webhooks/github
```

## Step 15: Open GitHub and Configure the Webhook

Open your repository in a browser.

Example repository:

```text
https://github.com/vvr273/git-webhook
```

Then:

1. Click `Settings`
2. Click `Webhooks`
3. Click `Add webhook`

Fill the form like this:

### Payload URL

```text
https://YOUR-NGROK-URL/webhooks/github
```

Example:

```text
https://example.ngrok-free.app/webhooks/github
```

### Content type

Choose:

```text
application/json
```

Do not choose form encoding.

### Secret

Paste the exact same secret value that you put in `.env` as `GITHUB_WEBHOOK_SECRET`.

### SSL verification

Leave the default secure setting on.

### Which events to send

Choose:

```text
Let me select individual events
```

Then select:
- Pushes
- Pull requests
- Pull request reviews
- Pull request review comments
- Workflow runs
- Deployments
- Deployment statuses

### Active

Keep `Active` checked.

Then click:

```text
Add webhook
```

## Step 16: Confirm the First Webhook Event

After saving, GitHub usually sends a `ping` event immediately.

Go back to the terminal where the app is running.

You may see logs there.

In another terminal, run:

```bash
curl http://127.0.0.1:8000/events
```

You should see a stored event with:
- `event_type` as `ping`
- your repository name

## Step 17: Trigger a Real GitHub Event

Now do something in GitHub that creates webhook traffic.

Examples:
- push a commit
- open a pull request
- review a pull request
- run GitHub Actions

The easiest one is a push.

If you already have Git connected locally, you can make a small change and push it.

Example:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
git status
git add README.md
git commit -m "Test webhook event"
git push
```

If the push succeeds, GitHub should send a `push` webhook.

## Step 18: View the Stored Events

To list all events:

```bash
curl http://127.0.0.1:8000/events
```

To view the summary:

```bash
curl http://127.0.0.1:8000/metrics/summary
```

To view one specific event:

```bash
curl http://127.0.0.1:8000/events/DELIVERY_ID_HERE
```

## Step 19: Access the SQLite Database Directly

The data is stored in:

- [github_webhooks.db](/home/think41/vishnu/roi/git-webhook/github_webhooks.db)

To open it with SQLite:

```bash
sqlite3 github_webhooks.db
```

Inside SQLite, run:

```sql
.tables
.schema github_events
SELECT id, delivery_id, event_type, repository_full_name, actor_login, occurred_at, received_at FROM github_events ORDER BY id DESC;
```

Exit SQLite:

```sql
.quit
```

## Step 20: Run Tests

To run the automated tests:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
pytest
```

## Common Problems and Fixes

### Problem: `curl: (7) Failed to connect to 127.0.0.1 port 8000`

Cause:
- FastAPI app is not running

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
- check GitHub webhook `Secret`
- they must match exactly
- restart `uvicorn` after editing `.env`

### Problem: GitHub webhook was created but no events arrive

Cause:
- ngrok is not running
- wrong ngrok URL
- webhook configured on the wrong repository
- wrong content type

Fix:
- run `ngrok http 8000`
- confirm the webhook URL ends with `/webhooks/github`
- confirm the repo is correct
- confirm content type is `application/json`

### Problem: `ngrok` command not found

Fix:

```bash
sudo snap install ngrok
```

Then configure authtoken and run it again.

### Problem: Git push asks for login or fails

Cause:
- GitHub authentication is not configured locally

Fix:
- authenticate with GitHub using your preferred method
- ensure you have permission to push to the target repository

## What You Should Keep Running During a Demo

During a live demo, keep these two running in separate terminals:

Terminal 1:

```bash
cd /home/think41/vishnu/roi/git-webhook
. .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
ngrok http 8000
```

Then use a third terminal for checks like:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/events
curl http://127.0.0.1:8000/metrics/summary
```

## Minimum Demo Flow

If you need the shortest working demo:

1. Start FastAPI
2. Start ngrok
3. Add the GitHub webhook
4. Confirm `ping`
5. Push one commit
6. Show `/events`
7. Show `/metrics/summary`
8. Point to `github_webhooks.db`

## What This Setup Achieves

Once complete, this setup allows you to:
- receive GitHub webhook events on your local machine
- verify that the events are authentic
- normalize the event metadata
- store the event history locally
- inspect the results through API endpoints or SQLite

