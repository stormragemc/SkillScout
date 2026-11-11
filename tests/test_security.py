import unittest
from skillscout.security import gate


def report(severity="NONE", complete=True):
    return {"execution_successful": True, "analysis_completeness": {
        "is_complete": complete, "status": "complete" if complete else "partial", "coverage_percent": 100},
        "risk_assessment": {"recommendation": "SAFE", "severity": "LOW", "max_issue_severity": severity},
        "issues": []}


class SecurityTests(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(gate(report(), 0)["status"], "eligible")

    def test_issue_overrides_aggregate(self):
        r = report()
        r["issues"] = [{"severity": "CRITICAL"}]
        self.assertEqual(gate(r, 0)["status"], "blocked")

    def test_unknown_incomplete_suppressed(self):
        for r in [{}, report(complete=False), report("UNKNOWN"), {**report(), "suppressed_count": 1},
                  {**report(), "analysis_completeness": None}]:
            self.assertEqual(gate(r, 0)["status"], "unverified")
        self.assertEqual(gate(report(), 1)["status"], "unverified")

    def test_medium(self):
        self.assertEqual(gate(report("MEDIUM"), 0)["status"], "review_required")
