import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.routers.workflows import get_notice_config, update_notice_config


class NoticeWorkflowConfigTests(unittest.TestCase):
    def _workflow(self):
        return SimpleNamespace(id=8, mode="template_native", notice_config={}, notice_config_version=1, notice_config_history=[])

    def test_saves_ba_az_configuration_and_increments_version(self):
        workflow = self._workflow()
        db = Mock()
        db.get.return_value = workflow
        payload = SimpleNamespace(model_dump=lambda: {
            "dimensions": {"source_field": "BA", "rule_field": "AZ", "rule_value": "发展人"},
            "rows": [{"row": 5, "key": "邓州"}],
            "metrics": {"daily": {"column": "E", "source_field": "W", "aggregate": "sum", "dimension_field": "BA"}},
            "totals": {},
            "execution_mode": "value",
        })
        result = update_notice_config(8, payload, db)
        self.assertEqual(result["version"], 2)
        self.assertEqual(workflow.notice_config["dimensions"]["source_field"], "BA")
        self.assertEqual(workflow.notice_config["dimensions"]["rule_field"], "AZ")

    def test_rejects_wrong_native_dimension(self):
        db = Mock()
        db.get.return_value = self._workflow()
        payload = SimpleNamespace(model_dump=lambda: {"dimensions": {"source_field": "H"}, "rows": [{"row": 5}], "metrics": {"x": {}}, "totals": {}, "execution_mode": "value"})
        with self.assertRaises(Exception):
            update_notice_config(8, payload, db)

    def test_reads_current_version(self):
        workflow = self._workflow()
        workflow.notice_config = {"dimensions": {"source_field": "BA"}}
        db = Mock()
        db.get.return_value = workflow
        result = get_notice_config(8, db)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["config"]["dimensions"]["source_field"], "BA")

    def test_preserves_previous_config_in_history(self):
        workflow = self._workflow()
        workflow.notice_config = {"dimensions": {"source_field": "BA"}}
        db = Mock()
        db.get.return_value = workflow
        payload = SimpleNamespace(model_dump=lambda: {"dimensions": {"source_field": "BA", "rule_field": "AZ"}, "rows": [{"row": 5}], "metrics": {"x": {}}, "totals": {}, "execution_mode": "value"})
        update_notice_config(8, payload, db)
        self.assertEqual(workflow.notice_config_history[0]["version"], 1)
        self.assertEqual(workflow.notice_config_history[0]["config"]["dimensions"]["source_field"], "BA")


if __name__ == "__main__":
    unittest.main()
