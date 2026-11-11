import tempfile
import unittest
from pathlib import Path

from skillscout.config import CREATORS, init, load, save
from skillscout.core import ScoutError, Store, skill_metadata, tree_hash


class CoreTests(unittest.TestCase):
    def test_init_discloses_and_preserves_choices(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(d)
            self.assertEqual(init(s)["instagram_sources"], ["@" + h for h in CREATORS])
            c = load(s)
            self.assertEqual(c["schedules"], [])
            c["creators"] = []
            save(s, c)
            init(s)
            self.assertEqual(load(s)["creators"], [])

    def test_metadata_and_content_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "SKILL.md"
            p.write_text("---\nname: small-skill\ndescription: >-\n  A useful skill.\n---\nDo work.\n")
            self.assertEqual(skill_metadata(p)["name"], "small-skill")
            old = tree_hash(Path(d))
            p.write_text(p.read_text() + "Changed")
            self.assertNotEqual(tree_hash(Path(d)), old)

    def test_state_ids_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(d)
            with self.assertRaises(ScoutError):
                s.save("../escape", "x", {})
            source = Path(d) / "source"
            source.mkdir()
            (source / "link").symlink_to(Path(d) / "private")
            with self.assertRaises(ScoutError):
                tree_hash(source)

