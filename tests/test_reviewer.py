import tempfile
import unittest
from skillscout.config import init, load
from skillscout.core import ScoutError, Store
from skillscout.reviewer import model_review


class ReviewerTests(unittest.TestCase):
    def test_remote_review_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(d)
            init(s)
            with self.assertRaises(ScoutError):
                model_review(s, load(s), "anything")
