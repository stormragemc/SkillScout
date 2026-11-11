import contextlib
import io
import json
import tempfile
import unittest
from skillscout.cli import main


class CliTests(unittest.TestCase):
    def invoke(self, home, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--home", home, *args])
        return code, json.loads(out.getvalue())["result"]

    def test_onboarding_preferences_and_schedule(self):
        with tempfile.TemporaryDirectory() as d:
            code, result = self.invoke(d, "init")
            self.assertEqual(code, 0)
            self.assertEqual(result["preferences"]["interests"], ["coding", "design"])
            self.assertEqual(len(result["instagram_sources"]), 5)
            self.assertFalse(result["preferences"]["instagram_enabled"])
            self.invoke(d, "creators", "remove", "nick_saraev")
            _, again = self.invoke(d, "init")
            self.assertEqual(len(again["instagram_sources"]), 4)
            self.invoke(d, "schedule", "set", "morning", "--at", "09:15", "--timezone", "Asia/Singapore")
            _, jobs = self.invoke(d, "schedule", "list")
            self.assertEqual(len(jobs["schedules"][0]["next_runs"]), 5)

    def test_source_link_does_not_add_creator(self):
        with tempfile.TemporaryDirectory() as d:
            self.invoke(d, "init")
            self.invoke(d, "reel", "https://instagram.com/reel/ABC123/", "--creator", "newcreator")
            _, result = self.invoke(d, "creators", "list")
            self.assertNotIn("@newcreator", result["creators"])
