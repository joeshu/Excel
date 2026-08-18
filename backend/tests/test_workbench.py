import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.services.workbench import build_workbench_summary


class WorkbenchTests(unittest.TestCase):
    def test_summary_contains_counts_attention_and_recent_tasks(self):
        db = Mock()
        db.scalars.side_effect = [
            Mock(all=lambda: [SimpleNamespace(id=1)]),
            Mock(all=lambda: [SimpleNamespace(id=2)]),
            Mock(all=lambda: [SimpleNamespace(quality_summary={"issue_count": 2})]),
            Mock(all=lambda: [SimpleNamespace(id=3, status="failed", workflow_id=2, data_source_id=1, finished_at=None)]),
        ]
        result = build_workbench_summary(db)
        self.assertEqual(result["counts"]["templates"], 1)
        self.assertEqual(result["attention"]["failed_tasks"], 1)
        self.assertEqual(result["attention"]["quality_issues"], 2)
