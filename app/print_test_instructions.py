from textwrap import dedent


def main() -> None:
    print(
        dedent(
            """
            GitHub Webhook Testing Service

            1. Run the API
               uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

            2. Expose it with ngrok
               ngrok http 8000

            3. Configure the GitHub webhook
               - Repository Settings -> Webhooks -> Add webhook
               - Payload URL: https://<ngrok-id>.ngrok-free.app/webhooks/github
               - Content type: application/json
               - Secret: same as GITHUB_WEBHOOK_SECRET

            4. Select these events
               - Pushes
               - Pull requests
               - Pull request reviews
               - Pull request review comments
               - Workflow runs
               - Deployments
               - Deployment statuses

            5. Test flows
               - Push a commit to trigger push
               - Open or update a PR to trigger pull_request
               - Submit a PR review to trigger pull_request_review
               - Add an inline PR review comment to trigger pull_request_review_comment
               - Run GitHub Actions to trigger workflow_run
               - Create a deployment to trigger deployment and deployment_status
            """
        ).strip()
    )


if __name__ == "__main__":
    main()
