import urllib.request
import json
import os
import sys

def get_json(url, token=None):
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Python-urllib/3.x')
        if token:
            req.add_header('Authorization', f'token {token}')
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error fetching {url}: {e.code} {e.reason}")
        if e.code == 403:
            print("Rate limit exceeded or forbidden. Check your GITHUB_TOKEN.")
        return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    repo_owner = os.getenv('REPO_OWNER', 'doggy8088')
    repo_name = os.getenv('REPO_NAME', 'Apptopia')
    token = os.getenv('GITHUB_TOKEN')

    if len(sys.argv) > 1:
        repo_owner = sys.argv[1]
    if len(sys.argv) > 2:
        repo_name = sys.argv[2]

    print(f"Fetching issues for {repo_owner}/{repo_name}...")

    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    issues_url = f"{api_url}/issues?state=open&per_page=100"

    issues = get_json(issues_url, token)

    if not issues:
        print("No issues found or error fetching issues.")
        return

    issues_data = []

    for issue in issues:
        # Skip pull requests
        if 'pull_request' in issue:
            continue

        number = issue['number']
        title = issue['title']
        body = issue['body']
        user = issue['user']['login']

        # Fetch comments
        comments_url = issue['comments_url']
        comments = get_json(comments_url, token)

        comment_list = []
        last_comment_user = None

        if comments:
            for comment in comments:
                comment_list.append({
                    'user': comment['user']['login'],
                    'body': comment['body'],
                    'created_at': comment['created_at']
                })
            last_comment_user = comments[-1]['user']['login']

        issues_data.append({
            'number': number,
            'title': title,
            'body': body,
            'user': user,
            'last_comment_user': last_comment_user,
            'comments': comment_list
        })

    # Output to stdout or file
    output_file = 'issues_data.json'
    with open(output_file, 'w') as f:
        json.dump(issues_data, f, indent=2)

    print(f"Fetched {len(issues_data)} issues. Data saved to {output_file}")

if __name__ == "__main__":
    main()
