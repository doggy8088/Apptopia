import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import time
import argparse

# --- Configuration ---
REPO_OWNER = "doggy8088"
REPO_NAME = "Apptopia"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "Triage-Agent"
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

API_BASE = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
MY_USERNAME = "doggy8088"  # Assuming I am the owner/maintainer

# Required sections from README.md
REQUIRED_SECTIONS = [
    "基本資訊",
    "需求定義",
    "驗收標準"
]

def log(msg):
    print(f"[Triage] {msg}")

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        log(f"HTTP Error {e.code}: {e.reason} for {url}")
        if e.code == 403:
             log("Rate limit likely exceeded or permission denied.")
        return None
    except Exception as e:
        log(f"Error: {e}")
        return None

def get_open_issues():
    issues = []
    page = 1
    while True:
        url = f"{API_BASE}/issues?state=open&per_page=100&page={page}"
        data = make_request(url)
        if not data:
            break
        # Filter out PRs, as the endpoint returns both issues and PRs
        page_issues = [i for i in data if "pull_request" not in i]
        if page_issues:
            issues.extend(page_issues)
        page += 1
    return issues

def get_issue_comments(issue_number):
    url = f"{API_BASE}/issues/{issue_number}/comments"
    return make_request(url) or []

def analyze_issue(issue, dry_run=True):
    number = issue["number"]
    title = issue["title"]
    body = issue["body"] or ""
    author = issue["user"]["login"]

    log(f"Analyzing Issue #{number}: {title}")

    comments = get_issue_comments(number)

    # 1. Check if the last comment is mine or bot's
    if comments:
        last_comment = comments[-1]
        last_commenter = last_comment["user"]["login"]
        if last_commenter == MY_USERNAME or "bot" in last_commenter.lower() or "github-actions" in last_commenter:
            log(f"  -> Skipping: Last comment is by {last_commenter}.")
            return
    else:
        # No comments yet, check if creator is me (unlikely for triage but good to handle)
        if author == MY_USERNAME:
            log(f"  -> Skipping: Issue created by me ({MY_USERNAME}).")
            return

    # 2. Analyze requirements
    missing_sections = []
    for section in REQUIRED_SECTIONS:
        if section not in body:
            missing_sections.append(section)

    is_clear = len(missing_sections) == 0

    if is_clear:
        log(f"  -> Requirements look clear. Preparing plan...")
        post_plan(issue, dry_run)
    else:
        log(f"  -> Requirements unclear. Missing: {', '.join(missing_sections)}")
        request_info(issue, missing_sections, dry_run)

def request_info(issue, missing_sections, dry_run=True):
    number = issue["number"]
    author = issue["user"]["login"]

    msg = (f"Hi @{author}, 感謝你的提案！\n\n"
           f"為了讓這個需求能更順利被實作，能否請你補充以下資訊？\n"
           f"- " + "\n- ".join(missing_sections) + "\n\n"
           f"參考 [README](https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/main/README.md#%E9%9C%80%E6%B1%82%E6%92%B0%E5%AF%AB%E8%A6%8F%E6%A0%BCissue-%E5%BF%85%E5%A1%AB) 的格式會非常有幫助。謝謝！")

    if dry_run:
        print(f"DEBUG: Would post comment on #{number}:\n---\n{msg}\n---")
    else:
        log(f"  -> Posting comment to request info on #{number}...")
        post_comment(number, msg)

def post_plan(issue, dry_run=True):
    number = issue["number"]

    plan = (f"## 開發計畫 (Draft)\n\n"
            f"根據需求，預計執行以下步驟：\n\n"
            f"### Scope\n"
            f"- [ ] TBD\n\n"
            f"### Acceptance criteria (verifiable)\n"
            f"- [ ] TBD\n\n"
            f"### Verification\n"
            f"- [ ] TBD\n\n"
            f"### Risks\n"
            f"- TBD\n\n"
            f"### Rollback notes\n"
            f"- TBD\n")

    if dry_run:
        print(f"DEBUG: Would post plan on #{number}:\n---\n{plan}\n---")
    else:
        log(f"  -> Posting plan on #{number}...")
        post_comment(number, plan)

def post_comment(issue_number, body):
    url = f"{API_BASE}/issues/{issue_number}/comments"
    make_request(url, method="POST", data={"body": body})

def main():
    parser = argparse.ArgumentParser(description="Triage GitHub issues.")
    parser.add_argument("--run", action="store_true", help="Actually post comments to GitHub.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Print actions without posting (default).")
    args = parser.parse_args()

    # If --run is specified, dry_run is False. Otherwise it's True.
    # Note: The argparse default for store_true is False.
    # If user runs without args: --run is False, --dry-run is True (default).
    # If user runs --run: --run is True.
    # We want dry_run to be True unless --run is specified.

    dry_run = not args.run

    log(f"Starting triage check (Dry Run: {dry_run})...")
    issues = get_open_issues()
    if issues is None:
        log("Failed to fetch issues. Exiting.")
        return

    log(f"Found {len(issues)} open issues.")

    for issue in issues:
        analyze_issue(issue, dry_run)
        # Sleep to avoid rate limits
        time.sleep(1)

if __name__ == "__main__":
    main()
