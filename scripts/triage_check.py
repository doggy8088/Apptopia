import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import time

# Defaults
DEFAULT_REPO = "doggy8088/Apptopia"
DEFAULT_USER = "doggy8088"

def get_json(url):
    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Python-Urllib-Triage")
        if os.environ.get("GITHUB_TOKEN"):
             req.add_header("Authorization", f"token {os.environ['GITHUB_TOKEN']}")

        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e.code} {e.reason}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []

def post_comment(repo, issue_number, body, dry_run=True):
    if dry_run or not os.environ.get("GITHUB_TOKEN"):
        print(f"\n  [DRY RUN] Would post comment to #{issue_number}:")
        print(f"  {'-'*20}")
        print(f"  {body}")
        print(f"  {'-'*20}\n")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("User-Agent", "Python-Urllib-Triage")
    req.add_header("Authorization", f"token {os.environ['GITHUB_TOKEN']}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            print(f"  Successfully posted comment to #{issue_number}")
    except Exception as e:
        print(f"  Failed to post comment: {e}")

def analyze_issue(issue, comments, target_user):
    """
    Analyzes an issue to determine if action is needed.
    Returns: (needs_action: bool, reason: str, conversation_text: str)
    """
    number = issue["number"]
    title = issue["title"]

    # Skip PRs
    if "pull_request" in issue:
        return False, f"Skipping PR #{number}: {title}", ""

    last_commenter = None

    if comments:
        last_commenter = comments[-1]["user"]["login"]
    else:
        last_commenter = issue["user"]["login"]

    # If the last commenter is the target user or a bot, we skip.
    if last_commenter in [target_user, "github-actions[bot]"]:
        return False, f"Skipping Issue #{number}: {title} (Last comment by {last_commenter})", ""

    # Construct full conversation text
    conversation = []
    conversation.append(f"Title: {title}")
    conversation.append(f"Author: {issue['user']['login']}")
    conversation.append(f"Body:\n{issue.get('body', '')}\n")

    for comment in comments:
        conversation.append(f"--- Comment by {comment['user']['login']} ---\n{comment['body']}\n")

    return True, f"NEEDS ACTION: Issue #{number}: {title}", "\n".join(conversation)

def main():
    parser = argparse.ArgumentParser(description="Triage GitHub issues.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repository owner/name")
    parser.add_argument("--user", default=DEFAULT_USER, help="User to skip if last commenter")
    parser.add_argument("--post", action="store_true", help="Post comments (requires GITHUB_TOKEN)")
    args = parser.parse_args()

    repo = args.repo
    target_user = args.user
    dry_run = not args.post

    print(f"Fetching open issues for {repo}...")
    api_url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=100"
    issues = get_json(api_url)

    if not issues:
        print("No issues found or error fetching issues.")
        return

    actionable_count = 0

    for issue in issues:
        number = issue["number"]
        comments_url = issue["comments_url"]

        if "pull_request" in issue:
            # Skip fetching comments for PRs
            print(f"Skipping PR #{number}")
            continue

        comments = get_json(comments_url)
        time.sleep(0.5) # Be polite to API

        needs_action, reason, conversation = analyze_issue(issue, comments, target_user)

        print(reason)

        if needs_action:
            print(f"{'='*40}")
            print(conversation)
            print(f"{'='*40}")

            # Here we would invoke LLM or heuristic to generate response
            # For now, we just suggest checking it
            suggested_response = "Status Update: I've reviewed this issue. [Insert specific analysis here]."
            post_comment(repo, number, suggested_response, dry_run=dry_run)

            actionable_count += 1

    print(f"\nTotal actionable issues: {actionable_count}")

if __name__ == "__main__":
    main()
