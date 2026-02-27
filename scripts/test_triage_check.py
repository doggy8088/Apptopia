import unittest
import sys
import os
import json
import urllib.request
import urllib.error
from unittest.mock import MagicMock, patch

# Ensure the parent directory is in the path to import triage_check
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import triage_check

class TestTriageCheck(unittest.TestCase):

    def setUp(self):
        # Reset any global state if necessary (none in this script)
        pass

    @patch("triage_check.make_request")
    def test_get_open_issues_success(self, mock_make_request):
        # Mock API response for issues
        # The script does `if "pull_request" not in i`
        # Issues do not have 'pull_request' key
        # PRs have 'pull_request' key
        mock_make_request.return_value = [
            {"number": 1, "title": "Issue 1", "body": "Body 1", "user": {"login": "user1"}}, # Issue (no pull_request key)
            {"number": 2, "title": "PR 1", "body": "Body 2", "user": {"login": "user2"}, "pull_request": {}}, # PR
            {"number": 3, "title": "Issue 2", "body": "Body 3", "user": {"login": "user3"}} # Issue
        ]

        # Call the function under test
        issues = triage_check.get_open_issues()

        self.assertEqual(len(issues), 2)
        self.assertEqual(issues[0]["number"], 1)
        self.assertEqual(issues[1]["number"], 3)

    def test_analyze_issue_skip_owner_comment(self):
        # We need to mock make_request inside analyze_issue
        with patch("triage_check.make_request") as mock_make_request:
            # Mock issue
            issue = {"number": 1, "title": "Test Issue", "body": "Body", "user": {"login": "user1"}}

            # Mock comments: Last one is by owner
            mock_make_request.return_value = [
                {"user": {"login": "user1"}, "body": "Comment 1"},
                {"user": {"login": triage_check.MY_USERNAME}, "body": "Owner comment"}
            ]

            # Capture log output
            with patch("builtins.print") as mock_print:
                triage_check.analyze_issue(issue, dry_run=True)
                expected_msg = f"[Triage]   -> Skipping: Last comment is by {triage_check.MY_USERNAME}."
                mock_print.assert_any_call(expected_msg)

    def test_analyze_issue_skip_bot_comment(self):
        with patch("triage_check.make_request") as mock_make_request:
            # Mock issue
            issue = {"number": 1, "title": "Test Issue", "body": "Body", "user": {"login": "user1"}}

            # Mock comments: Last one is by bot
            mock_make_request.return_value = [
                {"user": {"login": "user1"}, "body": "Comment 1"},
                {"user": {"login": "github-actions[bot]"}, "body": "Bot comment"}
            ]

            # Capture log output
            with patch("builtins.print") as mock_print:
                triage_check.analyze_issue(issue, dry_run=True)
                expected_msg = f"[Triage]   -> Skipping: Last comment is by github-actions[bot]."
                mock_print.assert_any_call(expected_msg)

    def test_analyze_issue_needs_info(self):
        with patch("triage_check.make_request") as mock_make_request:
            # Mock issue with missing sections
            issue = {"number": 1, "title": "Test Issue", "body": "Some body content but missing headers", "user": {"login": "user1"}}

            # No comments
            mock_make_request.return_value = []

            # Capture log output
            with patch("builtins.print") as mock_print:
                triage_check.analyze_issue(issue, dry_run=True)

                missing_str = "基本資訊, 需求定義, 驗收標準"
                expected_msg = f"[Triage]   -> Requirements unclear. Missing: {missing_str}"
                mock_print.assert_any_call(expected_msg)

    def test_analyze_issue_ready_for_plan(self):
        with patch("triage_check.make_request") as mock_make_request:
            # Mock issue with all sections
            body = """
            ### A. 基本資訊
            ...
            ### B. 需求定義
            ...
            ### C. 驗收標準
            ...
            """
            issue = {"number": 1, "title": "Test Issue", "body": body, "user": {"login": "user1"}}

            # No comments
            mock_make_request.return_value = []

            # Capture log output
            with patch("builtins.print") as mock_print:
                triage_check.analyze_issue(issue, dry_run=True)
                expected_msg = "[Triage]   -> Requirements look clear. Preparing plan..."
                mock_print.assert_any_call(expected_msg)

if __name__ == "__main__":
    unittest.main()
