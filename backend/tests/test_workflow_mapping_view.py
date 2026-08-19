import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.routers.workflows import workflow_mapping_rules


class WorkflowMappingViewTests(unittest.TestCase):
    def test_formula_workflow_returns_column_rules(self):
        workflow = SimpleNamespace(id=1, template_id=2, mode="formula", column_mapping={"通报!A": "地区"}, node_json={})
        template = SimpleNamespace(id=2, version="1.0", column_meta={"sheets": [{"title": "通报", "columns": [{"column": "A", "header": "地区", "type": "text"}]}]})
        db = Mock()
        db.get.side_effect = lambda model, key: workflow if key == 1 else template
        result = workflow_mapping_rules(1, db)
        self.assertEqual(result["rules"][0]["source_field"], "地区")

    def test_dag_workflow_returns_formula_and_condition_rules(self):
        workflow = SimpleNamespace(id=1, template_id=2, mode="dag", column_mapping={}, node_json={"nodes": [
            {"id": "formula", "type": "formula", "data": {"config": {"field": "合计", "expression": "金额 * 2"}}},
            {"id": "condition", "type": "condition", "data": {"config": {"field": "地区", "operator": "equals", "value": "华东"}}},
        ]})
        template = SimpleNamespace(id=2, version="1.0", column_meta={"sheets": []})
        db = Mock()
        db.get.side_effect = lambda model, key: workflow if key == 1 else template
        result = workflow_mapping_rules(1, db)
        self.assertEqual({rule["source_kind"] for rule in result["rules"]}, {"formula", "conditional"})
        self.assertEqual(result["rules"][0]["dependencies"], ["金额"])


if __name__ == "__main__":
    unittest.main()
