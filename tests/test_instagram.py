import json
import tempfile
import unittest
from unittest.mock import patch
from skillscout.config import DEFAULTS
from skillscout.core import ScoutError, Store
from skillscout.instagram import discover, normalize, reach_posts, reel_identity


class InstagramTests(unittest.TestCase):
    def test_identity(self):
        self.assertEqual(reel_identity("https://instagram.com/p/ABC123/?x=1"),
                         "https://www.instagram.com/reel/ABC123/")
        p = normalize({"url": "https://instagram.com/reel/ABC123/",
                       "caption": "Tool https://github.com/owner/repo"}, "nick_saraev")
        self.assertEqual(p["github_candidates"], ["owner/repo"])
        self.assertEqual(p["evidence_level"], "caption_only")

    def test_opt_in(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ScoutError):
                discover(Store(d), DEFAULTS)

    def test_actual_reach_envelope_contract(self):
        payload = {"schema_version": "1", "ok": True, "items": [{"shortcode": "ABC123"}]}
        with patch("skillscout.instagram.shutil.which", return_value="/fixture/agent-reach"):
            with patch("skillscout.instagram.command", return_value=(0, json.dumps(payload))):
                self.assertEqual(len(reach_posts("nick_saraev", 6)), 1)

    def test_deduplication(self):
        with tempfile.TemporaryDirectory() as d:
            c = {**DEFAULTS, "creators": ["nick_saraev"], "instagram_enabled": True}
            with patch("skillscout.instagram.reach_posts", return_value=[
                {"url": "https://instagram.com/reel/ABC123/", "caption": "new coding skill"}]):
                first = discover(Store(d), c)
                second = discover(Store(d), c)
            self.assertEqual(len(first["new_posts"]), 1)
            self.assertEqual(second["new_posts"], [])
            self.assertEqual(second["previously_seen"], 1)
