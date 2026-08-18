import json
import unittest
from types import SimpleNamespace

from app.services.task_batches import summarize_batches


class TaskBatchTests(unittest.TestCase):
    def test_groups_tasks_and_preserves_shared_notice_config(self):
        tasks = [
            SimpleNamespace(id=1, batch_id="batch-a", data_source_id=10, status="success", output_path="one.xlsx", notice_config=json.dumps({"title": "月报"}, ensure_ascii=False)),
            SimpleNamespace(id=2, batch_id="batch-a", data_source_id=11, status="failed", output_path=None, notice_config=json.dumps({"title": "月报"}, ensure_ascii=False)),
            SimpleNamespace(id=3, batch_id="batch-b", data_source_id=12, status="running", output_path=None, notice_config="{}"),
        ]
        summaries = summarize_batches(tasks)
        self.assertEqual([item["batch_id"] for item in summaries], ["batch-b", "batch-a"])
        self.assertEqual(summaries[1]["success_count"], 1)
        self.assertEqual(summaries[1]["failed_count"], 1)
        self.assertEqual(summaries[1]["notice_config"]["title"], "月报")
