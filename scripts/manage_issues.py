#!/usr/bin/env python3
import json
import os
import sys
import argparse
import urllib.request
import urllib.error
import re

# Default Configuration
DEFAULT_REPO = "doggy8088/Apptopia"
DEFAULT_USER = "doggy8088"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def get_headers():
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IssueManager/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

def parse_link_header(link_header):
    if not link_header:
        return None

    links = {}
    parts = link_header.split(',')
    for part in parts:
        section = part.split(';')
        if len(section) < 2:
            continue
        url = section[0].strip()[1:-1]
        rel_match = re.search(r'rel="([^"]+)"', section[1])
        if rel_match:
            rel = rel_match.group(1)
            links[rel] = url

    return links.get("next")

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method, headers=get_headers())
    if data:
        req.data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode()
            result = json.loads(content) if content else {}

            # If it's a list (GET issues/comments), return data + next_url
            if isinstance(result, list) and method == "GET":
                link_header = response.getheader("Link")
                next_url = parse_link_header(link_header)
                return result, next_url

            # If it's a dict (single object or POST response), just return result
            return result

    except urllib.error.HTTPError as e:
        print(f"Error making request to {url}: {e.code} {e.reason}")
        try:
            print(e.read().decode())
        except:
            pass
        return None
    except Exception as e:
        print(f"Error making request to {url}: {e}")
        return None

def get_all_items(url):
    all_items = []
    current_url = url

    while current_url:
        result = make_request(current_url)
        if result is None:
            break

        # Result is (data, next_url) tuple for lists
        if isinstance(result, tuple):
            items, next_url = result
            all_items.extend(items)
            current_url = next_url
        else:
            # Should not happen for lists if make_request logic is correct
            # But if API returns single object for some reason, handle it
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, dict): # Should not happen for list endpoints
                 all_items.append(result)
            current_url = None

    return all_items

def post_comment(issue_number, comment_body, repo):
    if not GITHUB_TOKEN:
        print("Cannot post comment: GITHUB_TOKEN not set.")
        return False

    url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
    print(f"Posting comment to {url}...")
    result = make_request(url, method="POST", data={"body": comment_body})
    if result:
        print("Comment posted successfully.")
        return True
    return False

def analyze_issue(title, body, comments):
    """
    Simulates sending the issue content to an LLM for analysis.
    In a fully automated system, this would call an LLM API.
    """
    if body is None:
        body = ""

    full_text = f"Title: {title}\nBody: {body}\n"
    for c in comments:
        c_body = c.get('body', '') or ''
        full_text += f"Comment by {c['user']['login']}: {c_body}\n"

    # Simple heuristic with Chinese keywords support
    # Keywords: Must, Should, 必選, 最好有, 需求, Requirement
    keywords = ["Must", "Should", "必選", "最好有", "需求", "Requirement"]
    found_keywords = [kw for kw in keywords if kw.lower() in full_text.lower()]

    if not found_keywords:
        return {
            "status": "unclear",
            "reason": "Missing clear requirements (Keywords like 'Must', 'Should', '必選' not found in discussion).",
            "suggested_comment": "需求說明似乎不完整。請補充「Must/必選」或「Should/最好有」的具體條件。"
        }

    # Generate a generic development plan
    plan_template = (
        "[自動分析] 需求規格似乎足夠明確。建議開發計畫如下：\n\n"
        "1. **專案初始化**：建立專案結構。\n"
        "2. **核心功能實作**：根據需求實作主要功能。\n"
        "3. **測試與驗證**：撰寫測試案例並驗證。\n"
        "4. **文件撰寫**：補充 README 與使用手冊。\n\n"
        "請確認此計畫是否合適，或進一步補充細節。"
    )

    return {
        "status": "needs_review",
        "reason": f"Found keywords: {found_keywords}. Automated analysis requires LLM integration for customized plan.",
        "suggested_comment": plan_template
    }

def process_issue(issue, repo, target_user, dry_run=True, auto_confirm=False):
    number = issue['number']
    title = issue['title']
    body = issue.get('body', '') or '' # Handle None body safely
    comments_url = issue['comments_url']
    user = issue['user']['login']

    print(f"Processing Issue #{number}: {title}")

    # Fetch comments (all pages)
    comments = get_all_items(comments_url)
    if comments is None:
        print("Failed to fetch comments.")
        return

    last_comment_user = None
    if comments:
        last_comment = comments[-1]
        last_comment_user = last_comment['user']['login']
    else:
        # If no comments, the issue creator is the last person to "speak"
        last_comment_user = user

    # Check if last comment is by the target user
    if last_comment_user == target_user:
        print(f"  Skipping: Last comment by target user '{target_user}'.")
        return

    print(f"  Last comment by: {last_comment_user}")

    # Analyze
    analysis = analyze_issue(title, body, comments)
    print(f"  Analysis Status: {analysis['status']}")
    print(f"  Reason: {analysis['reason']}")
    print(f"  Suggested Comment: \"{analysis['suggested_comment']}\"")

    if not dry_run:
        if auto_confirm:
            post_comment(number, analysis['suggested_comment'], repo)
        else:
            confirm = input(f"Post this comment to Issue #{number}? (y/n): ")
            if confirm.lower() == 'y':
                post_comment(number, analysis['suggested_comment'], repo)
            else:
                print("Skipped posting comment.")
    else:
        print("  [Dry Run] Comment would be posted if --no-dry-run was specified.")

def main():
    parser = argparse.ArgumentParser(description="Manage GitHub Issues")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repository owner/name")
    parser.add_argument("--user", default=DEFAULT_USER, help="Target user to skip if last commenter")
    parser.add_argument("--no-dry-run", action="store_true", help="Enable posting comments")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirmation (requires --no-dry-run)")

    args = parser.parse_args()

    if not GITHUB_TOKEN and args.no_dry_run:
        print("Warning: GITHUB_TOKEN not set. Posting comments will fail.")

    url = f"https://api.github.com/repos/{args.repo}/issues?state=open"
    issues = get_all_items(url)

    if not issues:
        print("No open issues found or error fetching issues.")
        return

    print(f"Found {len(issues)} open issues in {args.repo}.")

    for issue in issues:
        if 'pull_request' in issue:
            continue
        process_issue(issue, args.repo, args.user, dry_run=not args.no_dry_run, auto_confirm=args.yes)

if __name__ == "__main__":
    main()
