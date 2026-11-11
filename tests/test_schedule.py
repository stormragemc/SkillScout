import tempfile
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from skillscout.config import init, load, save
from skillscout.core import ScoutError, Store
from skillscout.schedule import make, run_due, slots, upcoming


class ScheduleTests(unittest.TestCase):
    def test_local_time(self):
        j = make("morning", "github", "09:15", "Asia/Singapore", "daily")
        self.assertEqual(upcoming(j, datetime(2026, 11, 11, 0, tzinfo=timezone.utc))[0],
                         "2026-11-11T09:15:00+08:00")

    def test_dst_and_invalid(self):
        with self.assertRaises(ScoutError):
            make("bad", "all", "25:00", "UTC", "daily")
        j = make("spring", "github", "02:30", "America/New_York", "daily")
        self.assertEqual(slots(j, datetime(2026, 3, 8, 12, tzinfo=timezone.utc), before=0, after=0), [])

    def test_five_weekly_previews(self):
        j = make("weekly", "github", "09:15", "UTC", "mon")
        self.assertEqual(len(upcoming(j, datetime(2026, 11, 11, tzinfo=timezone.utc))), 5)

    def test_due_once(self):
        with tempfile.TemporaryDirectory() as d:
            s = Store(d)
            init(s)
            c = load(s)
            c["schedules"] = [make("test", "github", "09:15", "Asia/Singapore", "daily")]
            save(s, c)
            with patch("skillscout.schedule.run", return_value={"id": "fixture", "status": "completed"}) as task:
                t = datetime(2026, 11, 11, 1, 16, tzinfo=timezone.utc)
                self.assertEqual(len(run_due(s, t)), 1)
                self.assertEqual(run_due(s, t), [])
                task.assert_called_once()
