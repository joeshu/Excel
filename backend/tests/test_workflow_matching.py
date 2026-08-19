import unittest
from types import SimpleNamespace

from app.services.workflow_matching import match_workflows


class WorkflowMatchingTests(unittest.TestCase):
    def test_field_order_does_not_change_score(self):
        source = SimpleNamespace(schema_={"amount": {"type": "number"}, "region": {"type": "text"}})
        workflows = [SimpleNamespace(id=1, name="通报", mode="formula", template_id=2, column_mapping={"A": "region", "B": "amount"})]
        templates = [SimpleNamespace(id=2, version="1.0")]
        self.assertEqual(match_workflows(source, workflows, templates)[0]["score"], 1.0)

    def test_dag_matches_formula_and_condition_fields(self):
        source = SimpleNamespace(schema_={"amount": {"type": "number"}, "region": {"type": "text"}})
        workflow = SimpleNamespace(id=2, name="DAG 通报", mode="dag", template_id=3, column_mapping={}, node_json={"nodes": [
            {"id": "formula", "type": "formula", "data": {"config": {"field": "total", "expression": "amount * 2"}}},
            {"id": "condition", "type": "condition", "data": {"config": {"field": "region", "operator": "equals", "value": "华东"}}},
            {"id": "write", "type": "write_template", "data": {"config": {"mapping": {"A": "total"}}}},
        ]})
        result = match_workflows(source, [workflow], [SimpleNamespace(id=3, version="1.0")])[0]
        self.assertEqual(result["missing_fields"], ["total"])
        self.assertEqual(result["score"], 0.6667)
