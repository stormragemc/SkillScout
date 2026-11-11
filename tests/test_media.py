import tempfile
import unittest
from pathlib import Path
from skillscout.core import ScoutError, Store
from skillscout.media import analyze


class MediaTests(unittest.TestCase):
    def test_playlist_input_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            playlist = Path(d) / "untrusted.m3u8"
            playlist.write_text("#EXTM3U\n")
            with self.assertRaises(ScoutError):
                analyze(Store(Path(d) / "state"), playlist, "https://instagram.com/reel/ABC123/")
