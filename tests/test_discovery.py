import io
import tempfile
import unittest
import zipfile
from pathlib import Path

from skillscout.core import ScoutError
from skillscout.github import extract_archive, rank, repository
from skillscout.inventory import bm25


class DiscoveryTests(unittest.TestCase):
    def test_url_identity(self):
        self.assertEqual(repository("https://github.com/a/b.git"), "a/b")
        for bad in ["https://evil.com/a/b", "a/..", "https://github.com@evil.com/a/b", "a/b;run"]:
            with self.assertRaises(ScoutError):
                repository(bad)

    def test_missing_history_is_unknown(self):
        result = rank({"name": "design-agent", "stargazers_count": 100}, {"available": False}, ["design"])
        self.assertNotIn("momentum", result["components"])
        self.assertAlmostEqual(sum(result["weights"].values()), 1)

    def test_small_accelerating_project_and_tiny_spike(self):
        meta = {"name": "coding-agent", "stargazers_count": 800}
        hot = rank(meta, {"available": True, "stars_per_day": 100, "acceleration": 20}, ["coding"])
        tiny = rank(meta, {"available": True, "stars_per_day": 2, "acceleration": 2}, ["coding"])
        self.assertTrue(hot["emerging"])
        self.assertFalse(tiny["emerging"])

    def test_archive_rejects_escape_and_case_collision(self):
        for names in [["repo/../escape"], ["repo/A.txt", "repo/a.txt"]]:
            raw = io.BytesIO()
            with zipfile.ZipFile(raw, "w") as z:
                for name in names:
                    z.writestr(name, "x")
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ScoutError):
                    extract_archive(raw.getvalue(), Path(d) / "snapshot")

    def test_bm25_prioritizes_matching_capability(self):
        scores = bm25("audio measurement", ["audio measurements and audio measurement", "restaurant bookings"])
        self.assertGreater(scores[0], scores[1])

