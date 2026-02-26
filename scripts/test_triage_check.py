import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from triage_check import analyze_issue

class TestTriageCheck(unittest.TestCase):

    def test_pr_skip(self):
        issue = {"number": 1, "title": "Test PR", "pull_request": {}, "user": {"login": "user1"}}
        comments = []
        needs_action, reason, conversation = analyze_issue(issue, comments, "target_user")
        self.assertFalse(needs_action)
        self.assertIn("Skipping PR", reason)

    def test_target_user_comment_skip(self):
        issue = {"number": 2, "title": "Test Issue", "user": {"login": "user1"}}
        comments = [{"user": {"login": "target_user"}, "body": "comment"}]
        needs_action, reason, conversation = analyze_issue(issue, comments, "target_user")
        self.assertFalse(needs_action)
        self.assertIn("Skipping Issue", reason)

    def test_bot_comment_skip(self):
        issue = {"number": 3, "title": "Test Issue", "user": {"login": "user1"}}
        comments = [{"user": {"login": "github-actions[bot]"}, "body": "comment"}]
        needs_action, reason, conversation = analyze_issue(issue, comments, "target_user")
        self.assertFalse(needs_action)
        self.assertIn("Skipping Issue", reason)

    def test_other_user_comment_action(self):
        issue = {"number": 4, "title": "Test Issue", "user": {"login": "user1"}}
        comments = [{"user": {"login": "other_user"}, "body": "comment"}]
        needs_action, reason, conversation = analyze_issue(issue, comments, "target_user")
        self.assertTrue(needs_action)
        self.assertIn("NEEDS ACTION", reason)
        self.assertIn("--- Comment by other_user ---", conversation)

    def test_no_comments_action(self):
        issue = {"number": 5, "title": "Test Issue", "user": {"login": "user1"}}
        comments = []
        needs_action, reason, conversation = analyze_issue(issue, comments, "target_user")
        self.assertTrue(needs_action)
        self.assertIn("NEEDS ACTION", reason)

if __name__ == '__main__':
    unittest.main()
