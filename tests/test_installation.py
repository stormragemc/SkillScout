import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from skillscout.config import init, load
from skillscout.core import ScoutError, Store, tree_hash
from skillscout.proposals import approve, install, prepare, review, rollback, subject


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.store = Store(self.base / "state")
        init(self.store)
        self.config = load(self.store)
        self.root = self.store.root / "quarantine" / "fixture"
        skill = self.root / "skills" / "sample-skill"
        skill.mkdir(parents=True)
        (self.root / "LICENSE").write_text("Fixture permission notice")
        (skill / "SKILL.md").write_text("---\nname: sample-skill\ndescription: Explain coding examples.\n---\nUse a small example.\n")
        source = {"id": "fixture", "path": str(self.root), "repository": "owner/repo",
                  "revision": "a" * 40, "content_hash": tree_hash(self.root)}
        for item in [
            patch("skillscout.proposals.snapshot", return_value=source),
            patch("skillscout.proposals.scan", side_effect=lambda p: {
                "status": "eligible", "content_hash": tree_hash(p), "mode": "fixture"}),
            patch("skillscout.config.default_skill_root", return_value=self.base / "installed")]:
            item.start()
            self.addCleanup(item.stop)

    def approved(self):
        p = prepare(self.store, self.config, "owner/repo")
        p = review(self.store, self.config, p["id"], "add", "Adds a missing coding capability.",
                   "Compared accessible inventory with the instructions. Runtime not tested.")
        return approve(self.store, self.config, p["id"], p["fingerprint"])

    def test_approval_required(self):
        p = prepare(self.store, self.config, "owner/repo")
        with self.assertRaises(ScoutError):
            install(self.store, self.config, p["id"])
        with self.assertRaises(ScoutError):
            approve(self.store, self.config, p["id"], p["fingerprint"])

    def test_install_license_and_rollback(self):
        p = self.approved()
        result = install(self.store, self.config, p["id"])
        dest = Path(result["destination"])
        self.assertEqual(tree_hash(dest), p["content_hash"])
        self.assertEqual(len(list((dest / "references/upstream-licenses").glob("*"))), 1)
        rollback(self.store, p["id"])
        self.assertFalse(dest.exists())

    def test_changed_content_blocks(self):
        p = self.approved()
        (subject(self.store, p) / "changed.md").write_text("changed")
        with self.assertRaises(ScoutError):
            install(self.store, self.config, p["id"])

    def test_changed_inventory_blocks(self):
        p = self.approved()
        rules = self.base / "RULES.md"
        rules.write_text("Current coding preferences")
        self.config["rules_files"] = [str(rules)]
        with self.assertRaises(ScoutError):
            install(self.store, self.config, p["id"])

    def test_destination_edits_preserved(self):
        p = self.approved()
        dest = Path(p["destination"])
        dest.mkdir(parents=True)
        (dest / "CUSTOM.md").write_text("Personal changes")
        with self.assertRaises(ScoutError):
            install(self.store, self.config, p["id"])
        self.assertTrue((dest / "CUSTOM.md").exists())

    def test_rollback_refuses_edits(self):
        p = self.approved()
        install(self.store, self.config, p["id"])
        (Path(p["destination"]) / "CUSTOM.md").write_text("Keep")
        with self.assertRaises(ScoutError):
            rollback(self.store, p["id"])


    def test_approved_work_export(self):
        import zipfile
        from skillscout.proposals import export_work
        self.config["delivery"] = "work"
        p = self.approved()
        output = self.base / "approved.zip"
        result = export_work(self.store, self.config, p["id"], output)
        self.assertFalse(result["installed"])
        with zipfile.ZipFile(output) as archive:
            self.assertIn("sample-skill/SKILL.md", archive.namelist())
        self.assertFalse((self.base / "installed").exists())

    def test_work_delivery_cannot_claim_local_install(self):
        self.config["delivery"] = "work"
        p = self.approved()
        with self.assertRaises(ScoutError):
            install(self.store, self.config, p["id"])


    def test_update_rollback_restores_files_and_tracking(self):
        import shutil
        old = self.approved()
        install(self.store, self.config, old["id"])
        destination = Path(old["destination"])
        old_hash = tree_hash(destination)
        new_root = self.store.root / "quarantine" / "fixture-two"
        shutil.copytree(self.root, new_root)
        manifest = new_root / "skills/sample-skill/SKILL.md"
        manifest.write_text(manifest.read_text() + "Also explain generators.\n")
        source = {"id": "fixture-two", "path": str(new_root), "repository": "owner/repo",
                  "revision": "b" * 40, "content_hash": tree_hash(new_root)}
        with patch("skillscout.proposals.snapshot", return_value=source):
            new = prepare(self.store, self.config, "owner/repo")
        new = review(self.store, self.config, new["id"], "update", "Adds useful generator examples.",
                     "Compared old instructions with new generator guidance; runtime not tested.")
        approve(self.store, self.config, new["id"], new["fingerprint"])
        install(self.store, self.config, new["id"])
        self.assertNotEqual(tree_hash(destination), old_hash)
        rollback(self.store, new["id"])
        self.assertEqual(tree_hash(destination), old_hash)
        self.assertEqual(self.store.load("installed", "sample-skill")["revision"], "a" * 40)
