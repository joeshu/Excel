import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.routers.tasks import task_mapping_trace


class TaskMappingTraceTests(unittest.TestCase):
    def test_trace_prefers_task_snapshot_rules(self):
        task = SimpleNamespace(id=9, workflow_id=7, data_source_id=4, mapping_snapshot_id=12)
        workflow = SimpleNamespace(id=7, template_id=3, name="通报流程", mode="formula", column_mapping={"通报!A": "地区"}, node_json={})
        template = SimpleNamespace(id=3, version="2.0", column_meta={"sheets": [{"title": "通报", "columns": [{"column": "A", "header": "地区", "type": "text"}]}]})
        snapshot = SimpleNamespace(id=12, rule_version=4, template_version="1.0", dependency_order=["金额", "合计"], validation_result={"valid": True}, rules=[{"target": "通报!A", "source_kind": "field", "source_field": "地区"}])
        db = Mock()
        db.get.side_effect = lambda model, key: {9: task, 7: workflow, 3: template, 12: snapshot}.get(key)
        result = task_mapping_trace(9, db)
        self.assertEqual(result["mapping_snapshot_id"], 12)
        self.assertEqual(result["mapping_rule_version"], 4)
        self.assertEqual(result["rules"][0]["source_field"], "地区")


if __name__ == "__main__":
    unittest.main()
